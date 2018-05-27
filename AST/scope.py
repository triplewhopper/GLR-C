from collections import OrderedDict
from AST import nodes
from typing import Generic, TypeVar, Optional

T = TypeVar('T')


class IParent(Generic[T]):
    """
    :type _parent: None|T
    """
    def __init__(self, parent: Optional[T] = None):
        if parent is None:
            self._parent = None
        else:
            assert isinstance(parent, T)
            self._parent = parent

    @property
    def parent(self):
        return self._parent


class IDepth(IParent):
    """
    :type _depth: int
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is None:
            self._depth = 0
        else:
            assert isinstance(parent, IDepth)
            self._depth = parent.depth + 1

    @property
    def depth(self):
        return self._depth


class IClassScope(IParent):
    pass


class ITagNameSpace(IParent['ITagNameSpace']):
    """
    :type __tagDeclInScope: dict[str,AST.nodes.TagDecl]
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__tagDeclInScope = OrderedDict()

    def __contains__(self, item: str):
        assert isinstance(item, str)
        return item in self.__tagDeclInScope

    def getDecl(self, tag: str):
        assert isinstance(tag, str)
        return self.__tagDeclInScope[tag]

    def getDeclRecursively(self, tag: str):
        if tag in self:
            return self.getDecl(tag)
        if self.parent is None:
            raise KeyError(tag)
        return self.parent.getDeclRecursively(tag)

    def insertRecordDecl(self, tag: str, env, isDefinition: bool = False):
        assert isinstance(tag, str)
        decl = nodes.RecordDecl(tag, env, isDefinition)
        if tag in self.__tagDeclInScope:
            prev = self.__tagDeclInScope[tag]
            if decl.isDefinition:
                if prev.isDefinition:
                    if prev.isBeingDefined:
                        raise RuntimeError('')


class OrdinaryIdentifierNameSpace(IParent):
    pass
