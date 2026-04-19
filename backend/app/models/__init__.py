"""Data models and schemas"""
# Export all schemas for easy importing
try:
    from .schemas import (
        ChatMessage,
        UserProfile,
        QuizQuestion,
        FlashCard,
        DiagnosticResult
    )
    __all__ = [
        "ChatMessage",
        "UserProfile",
        "QuizQuestion",
        "FlashCard",
        "DiagnosticResult"
    ]
except ImportError as e:
    # If imports fail, just expose the module
    __all__ = []

