from vp.cli import main

if __name__ == "__main__":
    main(
        sheets_dir="sheets",
        default_print_mode="cumulative",
        print_last_n=24,
        panic_hotcorner=True,
    )
