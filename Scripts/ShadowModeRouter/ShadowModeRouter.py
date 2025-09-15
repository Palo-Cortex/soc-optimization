demisto.debug('pack name = SOC Framework, pack version = 2.0.8')


def main():
    try:
        shadow_mode = demisto.args().get("ShadowMode")

        # Normalize to boolean
        shadow_mode = str(shadow_mode).strip().lower() in ("true", "1", "yes")

        route = "SHADOW MODE" if shadow_mode else "FULL MODE"

        # Print to war room
        return_results(route)

        # Set context so conditional can branch
        return_results(CommandResults(
            outputs_prefix="Shadow",
            outputs={"Route": route}
        ))

    except Exception as e:
        return_error(f"SOC_ShadowModeRouter failed: {str(e)}")

if __name__ in ("__main__", "__builtin__", "builtins"):
    main()

