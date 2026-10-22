#ifndef TEST_KERNEL_H
#define TEST_KERNEL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Deterministic host substitutes; ticks are milliseconds in this test only. */
typedef struct
{
    int64_t ticks;
} k_timeout_t;
typedef int64_t k_timepoint_t;
typedef int k_spinlock_key_t;
struct k_spinlock
{
    int unused;
};
struct k_thread
{
    int unused;
};
struct k_sem
{
    unsigned int count;
};

#define K_MSEC(value)                      ((k_timeout_t){(value)})
#define K_SECONDS(value)                   K_MSEC((value) * 1000)
#define K_NO_WAIT                          K_MSEC(0)
#define K_FOREVER                          K_MSEC(-1)
#define K_TIMEOUT_EQ(a, b)                 ((a).ticks == (b).ticks)
#define ARG_UNUSED(value)                  ((void)(value))
#define K_THREAD_STACK_DEFINE(name, size)  char name[size]
#define K_THREAD_STACK_SIZEOF(name)        sizeof(name)
#define K_SEM_DEFINE(name, initial, limit) struct k_sem name = {initial}

k_spinlock_key_t k_spin_lock(struct k_spinlock *lock);
void k_spin_unlock(struct k_spinlock *lock, k_spinlock_key_t key);
void k_sem_give(struct k_sem *sem);
int k_sem_take(struct k_sem *sem, k_timeout_t timeout);
int32_t k_sleep(k_timeout_t timeout);
k_timepoint_t sys_timepoint_calc(k_timeout_t timeout);
k_timeout_t sys_timepoint_timeout(k_timepoint_t deadline);
bool sys_timepoint_expired(k_timepoint_t deadline);
void k_thread_create(struct k_thread *thread, void *stack, size_t size, void (*entry)(void *, void *, void *), void *a, void *b, void *c, int priority, uint32_t options, k_timeout_t delay);
int k_thread_name_set(struct k_thread *thread, const char *name);
void k_thread_start(struct k_thread *thread);

#endif
