#ifndef SIMULATION_LOG_H
#define SIMULATION_LOG_H
#define LOG_LEVEL_INF 3
#define LOG_MODULE_REGISTER(name, level)
void simulation_log(const char *, ...);
#define LOG_INF(...) simulation_log(__VA_ARGS__)
#define LOG_WRN(...) simulation_log(__VA_ARGS__)
#define LOG_ERR(...) simulation_log(__VA_ARGS__)
#endif
