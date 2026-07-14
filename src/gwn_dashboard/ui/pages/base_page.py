"""Base class for Streamlit pages."""

from abc import ABC, abstractmethod


class BasePage(ABC):
    @property
    @abstractmethod
    def label(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def render(self) -> None:
        raise NotImplementedError
