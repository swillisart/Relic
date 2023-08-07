# Markdown Syntax Reference

Markdown is a plain-text way to style text documents.
The way to control how the document is displayed you can use a set of non-alphabetic characters illustrated below.

### Headers

```
# This is an <h1> tag
## This is an <h2> tag
##### This is an <h6> tag
```
### Emphasis
```
*this italic*
_also italic_
```

_Italicize_

```
**This bold**
__Also bold__
```

**Bold**

### Lists / Bullet Points

```
* Item 1
* Item 2
 * Item 2.1
 * Item 2.2
```

* Item 1
* Item 2
 * Item 2.1
 * Item 2.2


### Links
```
[GitHub](http://github.com) 
```
[GitHub](http://github.com) 
### Quote Blocks
Usually for notes or special attention:
```
> **Note**: this is super important
> information that is critical.
```
> **Note**: this is super important
> information that is critical.

### Tables
```
First Header   | Second Header
-------------- | ----------------
Content row 0  | Content column 1
Content row 1  | Content column 1
```
First Header   | Second Header
-------------- | ----------------
Content row 0  | Content column 1
Content row 1  | Content column 1

### Escaping
Use backslash escapes to generate literal characters which would otherwise have special meaning in Markdown’s formatting syntax.

`\*literal asterisks\* `


### Code Blocks
> **NOTE**: Triple backticks  `  
> backslashes "\" are merely for escaping. Normally it would simply be 3 ```

```
\```
def function(arg1, arg2):
    return arg1 + arg2
\```
```

