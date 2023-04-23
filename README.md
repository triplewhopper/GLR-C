# GLR-C
A simple interpreter based on GLR(1) implemented in Python (English follows).
## 预处理
* 没写。

## 词法分析
* 普通的token用`re`解决。
* 转义字符串的token手写了自动机解决（还好状态不多）。
* 数字用`re`结合手动判定解决（比如看看是否字面量溢出之类的）

## 语法分析
* 参照龙书LR(1)部分（没用LALR，内存不缺），但是写的其实是GLR(1)。两者不同在于后者维护了一张DAG，
相当于多个parse分支。如果两个分支reduce完了最顶上的状态看起来是一样的，那么就合并它们。怎么合并呢，DAG中的顶点维护一个前驱点集合，然后合并这个集合就好啦。
不过比较烦人的是必须保持生成的ParseTree节点与DAG节点的对应。比方说，现在我有A，B两分支，我要合并它们。但是呢A的前驱是AA，B的前驱是BB，你不能规约的时候
从原属于A的ParseTreeNode蹭蹭蹭跑到BB的ParseTreeNode上去了，那样就全乱套了。
* 再说规约。规约其实在这里变成了回溯，要顺着前驱上溯，试一试每条分支可不可以能不能行。这里又有一个问题。由于合并，DAG的一个点可能对应多个ParseTreeNode。
根据乘法原理，你得都试一遍。反正我是都试一遍。好像并不会慢（逃
* 细节很多很烦。
* 我给语法生成式上每一个非终结符都写了一个class。
* 非终结符的class构造的时候需要稍微判断一下剪掉那些一眼看出来不合文法的（比如悬空else，我的GLR本身没法剪掉）

## 生成AST

* 所谓的符号表是一边生成AST一边构造的。狗血的地方在于C的表达式和变量定义紧紧绑在一起，哦对还有鬼畜的类型。类型是可以递归的，然后struct和函数再来凑凑热闹。
* 类型检查就是得对着c语言标准抄。

## 生成代码
* 不做优化的话好像这部分是最好写的
* 就是十几个指令搞个栈式虚拟机。
* 求右值还是求左值是值得注意的。
* 但是还要注意跳转指令的生成。反正我是直接搞个空的`list`先填进去然后全完成了计算行号的时候再填。可变数据类型还是有优点的。

# GLR-C
A simple interpreter based on GLR(1) implemented in Python.

## Preprocessing
* Not implemented.

## Lexical Analysis
* Typical tokens are handled using `re`.
* Tokens for escape strings are handled using a handwritten automaton (luckily with a few states).
* Numbers are handled using `re` with manual checks (e.g. report error for literal overflow).

## Syntax Analysis
* Refer to the LR(1) analyzer part of *Compilers: Principles,Techniques,and Tools* (because it is easy to implement than LALR(1)), but we actually implemented a GLR(1) analyzer. The difference is that a GLR(1) analyzer maintains a directed acyclic Graph (DAG), equivalent to multiple parse branches. Any branches with the identical top state after reduction, are merged. To do this, we maintained a set of predecessor vertices for each vertex in the DAG, and merge corresponding sets. However, it is important to maintain correspondence between generated ParseTree nodes and DAG nodes. For example, suppose there are two branches (whose top node is A, B respectively) that need to be merged. If the predecessor of A is AA and the predecessor of B is BB, then you cannot simply move from the ParseTreeNode originally belonging to A, to the ParseTreeNode originally belonging to BB, as this would cause chaos.
* As for reduction, which actually becomes backtracking here, where you try to ascend along the predecessors to see if each branch is valid. Here is problem arises: since merging may occur, a point in the DAG may correspond to multiple ParseTreeNodes. According to the multiplication principle, there are many possible combinations. I enumerated them all, but it was still rather fast :)
* There are many details that need to be taken care of.
* I wrote a class for every non-terminal symbol in the grammar.
* When constructing an object of the non-terminals class, a useful optimization is to discard those obviously illeagal candidates (e.g. dangling `else`, which my GLR cannot handle).

## Generating AST
* The symbol table is constructed while generating the AST. The annoying thing is that C's expressions and variable definitions are tightly coupled, and oh, there are weird types too. Types can be recursive, and then structs and functions come together for the fun.
* Type checking is just copying from the C99 standard.

## Generating Code
* If no optimization is performed, this part seems to be the easiest to write.
* Just use a stack-based virtual machine with a dozen or so instructions.
* It is important to deal with lvalue and rvalue properly. 
* The jump instruction. A practical way is to use an empty mutable list as the jumping target, and then filled it in when after the line number had been calculated. Mutable data types still have their advantages.
