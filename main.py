"""Entry point: stdin → router → output → stdout"""
import sys
import json
import asyncio
import logging


async def main():
    # 0. Initialize logger (must be first)
    from loaders import config as config_loader
    from utils.logger import setup_logger, get_logger

    config = config_loader.load()
    logger_config = config.get("logging", {})
    setup_logger(logger_config)
    logger = get_logger("main")

    logger.info("Hook system starting")

    # 1. Read stdin (raw JSON)
    try:
        raw_payload = json.load(sys.stdin)
        event_name = raw_payload.get("hook_event_name", "unknown")
        logger.info(f"Received event: {event_name}")

        # Heavy payload logging only in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Raw payload: {json.dumps(raw_payload)}")
            if "tool_input" in raw_payload:
                logger.debug(f"Tool: {raw_payload.get('tool_name')}, Input: {raw_payload['tool_input']}")
            elif "prompt" in raw_payload:
                logger.debug(f"Prompt: {raw_payload['prompt']}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        print(json.dumps({
            'continue': False,
            'systemMessage': f'Invalid JSON input: {e}'
        }), file=sys.stdout)
        sys.exit(1)

    # 2. Schema validation (optional, requires jsonschema)
    try:
        from utils.schema_validator import validate_event
        error = validate_event(raw_payload)
        if error:
            logger.error(f"Schema validation failed: {error}")
            print(json.dumps({
                'continue': False,
                'systemMessage': f'Schema validation failed: {error}'
            }), file=sys.stdout)
            sys.exit(1)
        logger.debug("Schema validation passed")
    except ImportError:
        logger.warning("jsonschema not installed, skipping schema validation")

    # 3. Convert to typed object
    try:
        from utils.events import from_dict
        event = from_dict(raw_payload)
        logger.debug(f"Event object created: {type(event).__name__}")
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Failed to parse event object: {e}")
        print(json.dumps({
            'continue': False,
            'systemMessage': f'Invalid event data: {e}'
        }), file=sys.stdout)
        sys.exit(1)

    # 4. Set global event context (one-time)
    from utils.context import EventContext
    EventContext.set(event)
    logger.debug("Event context initialized")

    # 5. Load rules
    from loaders import rules as rules_loader
    rules = rules_loader.load()
    logger.info(f"Loaded {len(rules)} rules")

    # 6. Route and process (async)
    from router import route
    results = await route(rules)
    logger.debug(f"Router returned {len(results)} results")

    # 7. Merge and emit output
    from output import merge, emit
    result = merge(results)
    logger.debug("Results merged")

    # Log output before emitting
    if result:
        output_summary = {}
        if result.permission:
            output_summary['permission'] = result.permission
        if result.block is not None:
            output_summary['block'] = result.block
        if result.additional_context:
            output_summary['context_length'] = len(result.additional_context)
        if result.updated_input:
            output_summary['updated_input'] = result.updated_input
        if output_summary:
            logger.debug(f"Output: {output_summary}")

    emit(result, event.hook_event_name)


if __name__ == '__main__':
    asyncio.run(main())
