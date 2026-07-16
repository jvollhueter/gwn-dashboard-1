"""Base class for Streamlit pages."""

from abc import ABC, abstractmethod


class BasePage(ABC):
    """Abstract interface implemented by analytical page classes.
    
    Notes:
        The class is part of the documented public application architecture.
    """
    @property
    @abstractmethod
    def label(self) -> str:
        """Return the human-readable page label.
        
        Returns:
            str: Result produced by the operation.
        """
        raise NotImplementedError

    @abstractmethod
    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        raise NotImplementedError
