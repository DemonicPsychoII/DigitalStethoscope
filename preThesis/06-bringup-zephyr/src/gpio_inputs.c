#include "gpio_inputs.h"

#include <errno.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>

#include "app_events.h"
#include "app_logic.h"
#include "app_types.h"

LOG_MODULE_REGISTER(gpio_inputs, LOG_LEVEL_INF);

#define ZUSER DT_PATH(zephyr_user)
#define INPUT_DEBOUNCE_MS 25

static const struct gpio_dt_spec status_led = GPIO_DT_SPEC_GET(ZUSER, led_gpios);
static const struct gpio_dt_spec user_button = GPIO_DT_SPEC_GET(ZUSER, btn_gpios);
static const struct gpio_dt_spec switch_1 = GPIO_DT_SPEC_GET_BY_IDX(ZUSER, sw1_gpios, 0);
static const struct gpio_dt_spec switch_2 = GPIO_DT_SPEC_GET_BY_IDX(ZUSER, sw1_gpios, 1);
static const struct gpio_dt_spec switch_3 = GPIO_DT_SPEC_GET_BY_IDX(ZUSER, sw1_gpios, 2);

static struct gpio_callback button_callback;
static struct gpio_callback switch_gpio0_callback;
static struct gpio_callback switch_gpio1_callback;
static bool stable_button;
static int stable_switch;
static atomic_t deferred_errors;
static atomic_t button_edge_timestamp;
static atomic_t switch_edge_timestamp;

static void button_debounce_handler(struct k_work *work);
static void switch_debounce_handler(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(button_debounce_work, button_debounce_handler);
K_WORK_DELAYABLE_DEFINE(switch_debounce_work, switch_debounce_handler);

static int read_switch(void)
{
	int first = gpio_pin_get_dt(&switch_1);
	int second = gpio_pin_get_dt(&switch_2);
	int third = gpio_pin_get_dt(&switch_3);

	return app_switch_decode(first, second, third);
}

int gpio_inputs_probe_button_led(void)
{
	int rc;
	int pressed;

	if (!gpio_is_ready_dt(&status_led) || !gpio_is_ready_dt(&user_button)) {
		return -ENODEV;
	}
	rc = gpio_pin_configure_dt(&status_led, GPIO_OUTPUT_INACTIVE);
	if (rc != 0) {
		return rc;
	}
	rc = gpio_pin_configure_dt(&user_button, GPIO_INPUT);
	if (rc != 0) {
		return rc;
	}
	pressed = gpio_pin_get_dt(&user_button);
	if (pressed < 0) {
		return pressed;
	}
	stable_button = pressed != 0;
	return 0;
}

int gpio_inputs_probe_switch(void)
{
	const struct gpio_dt_spec *specs[] = {&switch_1, &switch_2, &switch_3};
	int rc;

	for (size_t i = 0; i < ARRAY_SIZE(specs); i++) {
		if (!gpio_is_ready_dt(specs[i])) {
			return -ENODEV;
		}
		rc = gpio_pin_configure_dt(specs[i], GPIO_INPUT);
		if (rc != 0) {
			return rc;
		}
	}
	stable_switch = read_switch();
	if (stable_switch < 0) {
		return stable_switch;
	}
	return stable_switch == 0 ? -ENODATA : 0;
}

void gpio_inputs_get_initial(bool *button_pressed, int *switch_position)
{
	if (button_pressed != NULL) {
		*button_pressed = stable_button;
	}
	if (switch_position != NULL) {
		*switch_position = stable_switch;
	}
}

static void schedule_debounce(struct k_work_delayable *work)
{
	int rc = k_work_reschedule(work, K_MSEC(INPUT_DEBOUNCE_MS));

	if (rc < 0) {
		atomic_inc(&deferred_errors);
	}
}

static void button_isr(const struct device *port, struct gpio_callback *callback,
                       gpio_port_pins_t pins)
{
	ARG_UNUSED(port);
	ARG_UNUSED(callback);
	ARG_UNUSED(pins);
	atomic_set(&button_edge_timestamp, (atomic_val_t)k_uptime_get_32());
	schedule_debounce(&button_debounce_work);
}

static void switch_isr(const struct device *port, struct gpio_callback *callback,
                       gpio_port_pins_t pins)
{
	ARG_UNUSED(port);
	ARG_UNUSED(callback);
	ARG_UNUSED(pins);
	atomic_set(&switch_edge_timestamp, (atomic_val_t)k_uptime_get_32());
	schedule_debounce(&switch_debounce_work);
}

static bool enqueue_event(const struct app_event *event)
{
	int rc = k_msgq_put(&app_event_queue, event, K_NO_WAIT);

	if (rc != 0) {
		uint32_t count = (uint32_t)atomic_inc(&deferred_errors) + 1U;

		if (app_should_log_failure(count)) {
			LOG_WRN("input event queue full (drops=%u, err=%d)", count, rc);
		}
	}
	return rc == 0;
}

static void button_debounce_handler(struct k_work *work)
{
	int pressed;
	struct app_event event = {
	        .type = APP_EVENT_BUTTON,
	        .timestamp_ms = (uint32_t)atomic_get(&button_edge_timestamp),
	};

	ARG_UNUSED(work);
	pressed = gpio_pin_get_dt(&user_button);
	if (pressed < 0) {
		LOG_ERR("button read after interrupt failed: %d", pressed);
		return;
	}
	if ((pressed != 0) == stable_button) {
		return;
	}
	event.data.button_pressed = pressed != 0;
	if (enqueue_event(&event))
		stable_button = pressed != 0;
	else
		schedule_debounce(&button_debounce_work);
}

static void switch_debounce_handler(struct k_work *work)
{
	int position;
	struct app_event event = {
	        .type = APP_EVENT_SWITCH,
	        .timestamp_ms = (uint32_t)atomic_get(&switch_edge_timestamp),
	};

	ARG_UNUSED(work);
	position = read_switch();
	if (position < 0) {
		LOG_ERR("switch read after interrupt invalid: %d", position);
		return;
	}
	if (position == stable_switch) {
		return;
	}
	event.data.switch_position = position;
	if (enqueue_event(&event))
		stable_switch = position;
	else
		schedule_debounce(&switch_debounce_work);
}

static int add_button_interrupt(gpio_flags_t interrupt_mode)
{
	int rc;

	gpio_init_callback(&button_callback, button_isr, BIT(user_button.pin));
	rc = gpio_add_callback(user_button.port, &button_callback);
	if (rc != 0) {
		return rc;
	}
	rc = gpio_pin_interrupt_configure_dt(&user_button, interrupt_mode);
	if (rc != 0) {
		int cleanup_rc = gpio_remove_callback(user_button.port, &button_callback);

		if (cleanup_rc != 0) {
			LOG_WRN("button callback cleanup failed: %d", cleanup_rc);
		}
	}
	return rc;
}

static int add_switch_interrupts(gpio_flags_t interrupt_mode)
{
	bool first_enabled = false;
	bool second_enabled = false;
	bool third_enabled = false;
	int rc;

	gpio_init_callback(&switch_gpio0_callback, switch_isr,
	                   BIT(switch_1.pin) | BIT(switch_2.pin));
	rc = gpio_add_callback(switch_1.port, &switch_gpio0_callback);
	if (rc != 0) {
		return rc;
	}
	gpio_init_callback(&switch_gpio1_callback, switch_isr, BIT(switch_3.pin));
	rc = gpio_add_callback(switch_3.port, &switch_gpio1_callback);
	if (rc != 0) {
		goto remove_first_callback;
	}
	rc = gpio_pin_interrupt_configure_dt(&switch_1, interrupt_mode);
	if (rc != 0) {
		goto rollback;
	}
	first_enabled = true;
	rc = gpio_pin_interrupt_configure_dt(&switch_2, interrupt_mode);
	if (rc != 0) {
		goto rollback;
	}
	second_enabled = true;
	rc = gpio_pin_interrupt_configure_dt(&switch_3, interrupt_mode);
	if (rc != 0) {
		goto rollback;
	}
	third_enabled = true;
	return 0;

rollback:
	if (third_enabled) {
		int cleanup_rc = gpio_pin_interrupt_configure_dt(&switch_3, GPIO_INT_DISABLE);

		if (cleanup_rc != 0) {
			LOG_WRN("switch 3 interrupt rollback failed: %d", cleanup_rc);
		}
	}
	if (second_enabled) {
		int cleanup_rc = gpio_pin_interrupt_configure_dt(&switch_2, GPIO_INT_DISABLE);

		if (cleanup_rc != 0) {
			LOG_WRN("switch 2 interrupt rollback failed: %d", cleanup_rc);
		}
	}
	if (first_enabled) {
		int cleanup_rc = gpio_pin_interrupt_configure_dt(&switch_1, GPIO_INT_DISABLE);

		if (cleanup_rc != 0) {
			LOG_WRN("switch 1 interrupt rollback failed: %d", cleanup_rc);
		}
	}
	{
		int cleanup_rc = gpio_remove_callback(switch_3.port, &switch_gpio1_callback);

		if (cleanup_rc != 0) {
			LOG_WRN("switch callback 1 rollback failed: %d", cleanup_rc);
		}
	}
remove_first_callback: {
	int cleanup_rc = gpio_remove_callback(switch_1.port, &switch_gpio0_callback);

	if (cleanup_rc != 0) {
		LOG_WRN("switch callback 0 rollback failed: %d", cleanup_rc);
	}
}
	return rc;
}

int gpio_inputs_start_button(gpio_flags_t interrupt_mode)
{
	int rc = add_button_interrupt(interrupt_mode);

	if (rc != 0) {
		LOG_ERR("button interrupt setup failed: %d", rc);
	}
	return rc;
}

int gpio_inputs_start_switch(gpio_flags_t interrupt_mode)
{
	int rc = add_switch_interrupts(interrupt_mode);

	if (rc != 0) {
		LOG_ERR("switch interrupt setup failed: %d", rc);
	}
	return rc;
}

int gpio_inputs_set_led(bool enabled)
{
	int rc = gpio_pin_set_dt(&status_led, enabled ? 1 : 0);

	if (rc != 0) {
		LOG_ERR("LED write failed (enabled=%d): %d", enabled, rc);
	}
	return rc;
}

#if DT_NODE_HAS_PROP(ZUSER, speed_gpios)
static const struct gpio_dt_spec speed_pins[] = {
        GPIO_DT_SPEC_GET_BY_IDX(ZUSER, speed_gpios, 0),
        GPIO_DT_SPEC_GET_BY_IDX(ZUSER, speed_gpios, 1),
        GPIO_DT_SPEC_GET_BY_IDX(ZUSER, speed_gpios, 2),
};
static struct gpio_callback speed_callbacks[3];
static atomic_t speed_timestamp;
static int stable_speed;
static void speed_handler(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(speed_work, speed_handler);
static void speed_isr(const struct device *dev, struct gpio_callback *cb, gpio_port_pins_t pins)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);
	atomic_set(&speed_timestamp, k_uptime_get_32());
	schedule_debounce(&speed_work);
}
static void speed_handler(struct k_work *work)
{
	ARG_UNUSED(work);
	int position =
	        app_switch_decode(gpio_pin_get_dt(&speed_pins[0]), gpio_pin_get_dt(&speed_pins[1]),
	                          gpio_pin_get_dt(&speed_pins[2]));
	if (position <= 0 || position == stable_speed)
		return;
	struct app_event e = {.type = APP_EVENT_SPEED,
	                      .timestamp_ms = (uint32_t)atomic_get(&speed_timestamp)};
	e.data.switch_position = position;
	if (enqueue_event(&e))
		stable_speed = position;
	else
		schedule_debounce(&speed_work);
}
#endif
int gpio_inputs_start_speed(void)
{
#if DT_NODE_HAS_PROP(ZUSER, speed_gpios)
	size_t configured = 0;
	int rc = 0;
	for (size_t i = 0; i < ARRAY_SIZE(speed_pins); i++) {
		if (!gpio_is_ready_dt(&speed_pins[i])) {
			rc = -ENODEV;
			goto fail;
		}
		rc = gpio_pin_configure_dt(&speed_pins[i], GPIO_INPUT);
		if (rc)
			goto fail;
		gpio_init_callback(&speed_callbacks[i], speed_isr, BIT(speed_pins[i].pin));
		rc = gpio_add_callback(speed_pins[i].port, &speed_callbacks[i]);
		if (rc)
			goto fail;
		configured++;
		rc = gpio_pin_interrupt_configure_dt(&speed_pins[i], GPIO_INT_EDGE_BOTH);
		if (rc)
			goto fail;
	}
	atomic_set(&speed_timestamp, k_uptime_get_32());
	schedule_debounce(&speed_work);
	return 0;
fail:
	for (size_t i = 0; i < configured; i++) {
		int disable_rc = gpio_pin_interrupt_configure_dt(&speed_pins[i], GPIO_INT_DISABLE);
		int remove_rc = gpio_remove_callback(speed_pins[i].port, &speed_callbacks[i]);
		if (disable_rc || remove_rc)
			LOG_WRN("Speed switch cleanup: %d/%d", disable_rc, remove_rc);
	}
	return rc;
#else
	return 0;
#endif
}
