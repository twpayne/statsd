Yet Another `statsd` Client
===========================


Clients
-------

```python
from statsd import Statsd
```

```python
statsd = Statsd()
```

```python
statsd = Statsd(host='stats.mydomain.com')
```

```python
statsd = Statsd(bucket_prefix='myapplication')
```

```python
statsd = Statsd(buffer_size=256)
```


Counters
--------

```python
statsd.count('mycounter', 1)
```

```python
counter = statsd.counter('mycounter')
counter += 1
```

```python
with statsd.count('active_connections'):
    # handle connection
```


Gauges
------

```python
statsd.gauge('volume', 11)
```

```python
statsd['volumne'] = 11
```


Timers
------

```python
statsd.timer('process', 0.234)
```

```python
with statsd.timer('process'):
   # ...
```

```python
with statsd.timer('manysteps') as t:
    part1()
    t.split('part1')
    part2()
    t.split('part2')
```

Children
--------

```python
submodule_statsd = statsd.child('submodule')
submodule_statsd.count('success', 1)
```
