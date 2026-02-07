.PHONY: help install install-dev test test-all security security-fix audit audit-dev clean dev start

# Default target
help:
	@echo "RadioCalico Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install         - Install all dependencies"
	@echo "  make install-dev     - Install development dependencies"
	@echo "  make test            - Run JavaScript tests (frontend + express)"
	@echo "  make test-all        - Run all tests including Python"
	@echo "  make security        - Run security audit (npm audit)"
	@echo "  make audit           - Alias for security"
	@echo "  make audit-dev       - Audit development dependencies only"
	@echo "  make security-fix    - Run npm audit fix (auto-fix vulnerabilities)"
	@echo "  make clean           - Clean node_modules and build artifacts"
	@echo "  make dev             - Start development servers"
	@echo "  make start           - Start production server"

# Install dependencies
install:
	npm install

install-dev:
	npm install --include=dev

# Testing
test:
	npm test

test-all:
	npm run test:all

# Security scanning
security:
	npm audit

audit: security

audit-dev:
	npm run audit:dev

security-fix:
	npm audit fix
	@echo ""
	@echo "Note: Some vulnerabilities may require manual updates."
	@echo "Run 'npm audit' again to check remaining issues."

# Clean
clean:
	rm -rf node_modules/
	@echo "Cleaned node_modules"

# Development
dev:
	npm run dev

start:
	npm start
