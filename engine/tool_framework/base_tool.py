from typing import Dict, Any, Optional, Callable
import inspect

class BaseTool:
    """Base class for all tools"""
    description = "Base tool class"

    def __init__(self):
        self._name = self.__class__.__name__
        self._description = self.__doc__ or "No description available"
        self._method_docs = {}
        self._methods = self._register_methods()

    def _register_methods(self) -> Dict[str, Callable]:
        """Register all public methods as tool methods"""
        methods = {}
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if not name.startswith('_'):
                methods[name] = method
                self._method_docs[name] = method.__doc__ or "No description available"
        return methods

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def methods(self) -> Dict[str, Callable]:
        """Get all registered methods"""
        return self._methods

    def get_method_description(self, method_name: str) -> str:
        """Get description for a specific method"""
        return self._method_docs.get(method_name, "No description available") 