Cookbook
========

Пример создания и использования feature flag:

.. code-block:: python

   from flags import FeatureFlagStore

   store = FeatureFlagStore()
   store.create_flag('new_ui', enabled=False)
   flag = store.get_flag('new_ui')
   print(flag)
   store.close()

Пример построения графика доверительных интервалов:

.. code-block:: python

    from stats.ab_test import run_sequential_analysis

    steps, pocock_alpha = run_sequential_analysis(
        ua=1000, ca=50, ub=1000, cb=60, alpha=0.05, looks=5
    )
    for step in steps:
        print(step["p_value_ab"])
