from src.listings import load_listings, validate_listings


def main():
    listings = load_listings()
    errors = validate_listings(listings)

    if errors:
        print("ERRORS")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Validated {len(listings)} listing(s).")


if __name__ == "__main__":
    main()
