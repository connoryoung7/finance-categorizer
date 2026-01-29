from services.pii_redactor import PIIRedactor

def main():
    pii_redactor = PIIRedactor()
    sample_text = "Hello, my name is John Doe. My address is 123 Main St, Anytown, USA. You can reach me at 908 212-3456."

    redacted_text = pii_redactor.redact_pii(sample_text)
    print("Original Text:")
    print(sample_text)
    print("\nRedacted Text:")
    print(redacted_text)

if __name__ == "__main__":
    main()