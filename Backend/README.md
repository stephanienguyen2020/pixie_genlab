# Pixie AI

## Getting started

### Setting Up:

- Clone this repository
- Create environment settings: `cp .env.example .env`
- Fill in the required environment variables in the `.env` file. Make sure you have MongoDB, Hume, Resend, and Google Gemini API Keys.
- Install required dependencies: `make install`

### Instructions: 
1. To create new patient or nurse, read `unit_test.py`, edit and run it.
2. Run the chat: `make chat`
3. Get the Streamlit UI: `make run`

- All PDF records will be saved in `records` folder.
- All QR code will be saved in `qr_code` folder.

## Contributing

We welcome contributions to this project! If you have experience in AI, NLP, or healthcare software development, feel free to:

Fork the repository and create a pull request with your contributions. Raise issues to report bugs or suggest improvements.

## License

<h2>License</h2>
Released under <a href="/LICENSE">MIT</a> by <a href="https://github.com/chrislevn">@chrislevn</a>.

## Disclaimer

This AI assistant is intended as a tool to support nurses and patients. It should not be used as a replacement for professional medical advice or diagnosis.
