"""
normtrace -- IHR Normative Observatory analytical core

This package encodes the analytical framework for NormTrace-IHR.
The LLM is used as an extraction engine; the framework itself lives here.

Main components:
  normtrace.ihr.articles  -- IHR article objects with selection criteria
  normtrace.ihr.scoring   -- C1 scoring engine (pure functions, no LLM)
  normtrace.ihr.prompts   -- Prompt construction from article objects
  normtrace.ihr.schema    -- LLM output validation
"""

__version__ = "1.0.0"
__author__ = "Adela B. Santos-Dominguez"
