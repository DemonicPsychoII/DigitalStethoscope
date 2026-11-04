#ifndef SIMULATION_KERNEL_H
#define SIMULATION_KERNEL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#define BIT(number)       (1U << (number))
#define ARRAY_SIZE(array) (sizeof(array) / sizeof((array)[0]))
#define ARG_UNUSED(value) ((void)(value))
#define __unused          __attribute__((__unused__))

#define NSEC_PER_USEC 1000U
#define NSEC_PER_MSEC 1000000U
#define USEC_PER_MSEC 1000U
#define USEC_PER_SEC  1000000U
#define NSEC_PER_SEC  1000000000U

typedef struct
{
    int64_t ticks;
} k_timeout_t;

typedef int64_t k_timepoint_t;
#define K_MSEC(milliseconds)        ((k_timeout_t){(milliseconds)})
#define K_SECONDS(seconds)          K_MSEC((int64_t)(seconds) * 1000)
#define K_NO_WAIT                   K_MSEC(0)
#define K_FOREVER                   K_MSEC(-1)
#define K_TIMEOUT_EQ(first, second) ((first).ticks == (second).ticks)

struct k_thread
{
    int unused;
};

struct k_spinlock
{
    int unused;
};

typedef int k_spinlock_key_t;

struct k_sem
{
    unsigned count;
    unsigned limit;
};

#define K_SEM_DEFINE(name, initial, maximum) struct k_sem name = {initial, maximum}
#define K_THREAD_STACK_DEFINE(name, size)    char name[size]
#define K_THREAD_STACK_SIZEOF(name)          sizeof(name)
typedef void (*simulation_entry)(void *, void *, void *);
struct k_thread *k_thread_create(struct k_thread *, char *, size_t, simulation_entry, void *, void *, void *, int, uint32_t, k_timeout_t);
int k_thread_name_set(struct k_thread *, const char *);
void k_thread_start(struct k_thread *);
int k_sem_take(struct k_sem *, k_timeout_t);
void k_sem_give(struct k_sem *);
k_spinlock_key_t k_spin_lock(struct k_spinlock *);
void k_spin_unlock(struct k_spinlock *, k_spinlock_key_t);
int k_sleep(k_timeout_t);
k_timepoint_t sys_timepoint_calc(k_timeout_t);
bool sys_timepoint_expired(k_timepoint_t);
k_timeout_t sys_timepoint_timeout(k_timepoint_t);

struct k_mutex
{
    int unused;
};

#define K_MUTEX_DEFINE(name) struct k_mutex name
int k_mutex_lock(struct k_mutex *, k_timeout_t);
int k_mutex_unlock(struct k_mutex *);
void k_sem_reset(struct k_sem *);

struct k_event
{
    uint32_t events;
};

#define K_EVENT_DEFINE(name) struct k_event name
uint32_t k_event_wait(struct k_event *, uint32_t, bool, k_timeout_t);
uint32_t k_event_test(struct k_event *, uint32_t);
uint32_t k_event_post(struct k_event *, uint32_t);
uint32_t k_event_clear(struct k_event *, uint32_t);
struct k_work;
typedef void (*k_work_handler_t)(struct k_work *);

struct k_work
{
    k_work_handler_t handler;
};

struct k_work_q
{
    int unused;
};

struct k_work_queue_config
{
    const char *name;
};

void k_work_init(struct k_work *, k_work_handler_t);
void k_work_queue_start(struct k_work_q *, char *, size_t, int, const struct k_work_queue_config *);
int k_work_submit_to_queue(struct k_work_q *, struct k_work *);
int64_t k_uptime_ticks(void);
uint64_t k_ticks_to_us_floor64(uint64_t);

typedef int atomic_t;

static inline int atomic_get(const atomic_t *value)
{
    return *value;
}

static inline void atomic_set(atomic_t *destination, int value)
{
    *destination = value;
}
#endif
