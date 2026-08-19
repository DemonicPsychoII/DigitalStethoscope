#include <zephyr/ztest.h>

ZTEST(stethoscope_ci_contract, test_required_suite_executes)
{
	zassert_true(true, "required native_sim contract suite did not execute");
}

ZTEST_SUITE(stethoscope_ci_contract, NULL, NULL, NULL, NULL, NULL);
