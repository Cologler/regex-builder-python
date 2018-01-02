# regex builder

save you from regex hell.

``` cmd
>>> python
>>> from regex_builder import RegexBuilder
>>> builder = RegexBuilder()
>>> expr = builder.int_range(13, 255).reduce().compile()
>>> print(expr)
... 1[3-9]|[2-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]
```

## similar tools

* [regexmagic](https://www.regexmagic.com/) (US$ 39.95)
