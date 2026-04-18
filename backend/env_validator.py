import os
import sys


class EnvValidator:
    def validate(self) -> list[str]:
        errors: list[str] = []

        llm_provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        groww_api_key = os.getenv("GROWW_API_KEY", "").strip()
        groww_api_secret = os.getenv("GROWW_API_SECRET", "").strip()
        database_url = os.getenv("DATABASE_URL", "").strip()
        mode = os.getenv("MODE", "").strip().lower()
        aws_region = os.getenv("AWS_REGION", "").strip()

        if llm_provider not in {"anthropic", "bedrock"}:
            errors.append(
                f"LLM_PROVIDER must be 'anthropic' or 'bedrock', got: {llm_provider}"
            )

        if llm_provider != "bedrock" and not anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")

        if not groww_api_key:
            errors.append("GROWW_API_KEY is required for Groww API access")

        if not groww_api_secret:
            errors.append("GROWW_API_SECRET is required for token generation")

        if database_url and not (
            database_url.startswith("sqlite:///")
            or database_url.startswith("postgresql://")
        ):
            errors.append("DATABASE_URL format invalid. Use sqlite:/// or postgresql://")

        if mode and mode not in {"paper", "live"}:
            errors.append(f"MODE must be 'paper' or 'live', got: {mode}")

        if llm_provider == "bedrock" and not aws_region:
            errors.append("AWS_REGION is required when LLM_PROVIDER=bedrock")

        return errors

    def validate_and_exit(self) -> None:
        errors = self.validate()
        if errors:
            print("\n❌ Environment validation failed:")
            for error in errors:
                print(f"  • {error}")
            print("\nCheck your .env file and try again.\n")
            sys.exit(1)

        print("✅ Environment validation passed")


env_validator = EnvValidator()
