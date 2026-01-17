# 🗺️ Roadmap

**Planned improvements and enhancements**

[![Status](https://img.shields.io/badge/Status-Planned-yellow)](./roadmap.md)
[![Version](https://img.shields.io/badge/Version-Future-blue)](./roadmap.md)

---

## 📋 Overview

This document lists planned improvements and enhancements for Trading Research Assistant. These features are **not currently implemented**. The order of items does not indicate implementation timelines or priorities.

---

## 🤖 LLM Providers and Routing

- **OpenAI API provider**
  
  Add OpenAI API integration as a new LLM provider option. Enables access to GPT models for analysis tasks.

- **Gemini API provider**
  
  Add Google Gemini API integration as a new LLM provider option. Provides alternative model choices for routing.

- **Perplexity API provider**
  
  Add Perplexity API integration as a new LLM provider option. Enables access to Perplexity models for research tasks.

- **OpenAI-compatible local gateway support**
  
  Support for local gateways like vLLM or LM Studio that expose OpenAI-compatible endpoints. Allows using local models with existing API provider infrastructure.

- **Model name validation against provider expectations**
  
  Validate model names at configuration time to ensure they match provider requirements. Prevents runtime errors from invalid model identifiers.

- **Streaming responses option**
  
  Add support for streaming LLM responses. Improves perceived latency for long-running analysis tasks.

- **Router profiles (lite/balanced/large)**
  
  Predefined routing profiles that select appropriate models based on available resources. Simplifies configuration for different hardware setups.

- **Improved fallback transparency in logs**
  
  Enhanced logging that clearly shows which provider/model was attempted and why fallback occurred. Improves debugging of routing decisions.

---

## ✅ Quality, Verification, and Robustness

- **Rate limiting and retry policy**
  
  Configurable rate limiting and retry policies per provider. Prevents API quota exhaustion and handles transient failures gracefully.

- **Result caching layer**
  
  Caching layer for news and LLM responses to avoid redundant API calls. Reduces costs and improves response times for repeated queries.

- **Enhanced verification rules**
  
  Expandable set of verification rules for detecting policy violations and unsupported claims. Improves output quality and compliance.

- **Input validation and sanitization**
  
  Comprehensive validation of user inputs and market data before processing. Prevents errors from malformed or unexpected data.

---

## 📦 Packaging and Deployment

- **Dockerfile and docker-compose**
  
  Containerization support with Dockerfile and docker-compose configuration. Simplifies deployment and environment consistency.

- **Preflight command improvements**
  
  Enhanced preflight checks with better diagnostics and automatic remediation suggestions. Helps identify configuration issues before runtime.

- **Installation script for Windows**
  
  Automated installation script that sets up dependencies and environment. Reduces manual setup steps for new users.

- **Configuration validation tool**
  
  Standalone tool to validate .env configuration without running the full application. Catches configuration errors early.

---

## 🎨 UX and Interfaces

- **Web UI dashboard**
  
  Web-based dashboard for viewing analysis results, recommendations, and system status. Provides better visualization than CLI output.

- **CLI interactive mode**
  
  Guided interactive setup mode for initial configuration. Helps users configure the system step by step.

- **Export reports (markdown/json)**
  
  Export analysis results and recommendations in markdown or JSON formats. Enables integration with external tools and documentation.

- **Progress indicators for long operations**
  
  Visual progress indicators for model downloads, analysis runs, and other long-running operations. Improves user experience during waits.

---

## 📊 Observability and Operations

- **Metrics and telemetry**
  
  Prometheus/OpenTelemetry integration for collecting system metrics. Enables monitoring and alerting in production environments.

- **Log correlation ID and trace ID**
  
  Correlation IDs and trace IDs in logs to track requests across components. Simplifies debugging of distributed operations.

- **Health checks endpoint and status report**
  
  HTTP endpoint for health checks and detailed status reports. Enables integration with monitoring systems and load balancers.

- **Structured error reporting**
  
  Structured error messages with error codes and context. Improves error diagnosis and support workflows.

---

[📖 Back to README](../../README.md) | [📚 Usage Guide](./usage_guide.md) | [🏗️ Architecture](./architecture.md)
