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

   from plots import plot_confidence_intervals

   data_a = [1, 2, 3]
   data_b = [3, 4, 5]
   plot_confidence_intervals(data_a, data_b)
