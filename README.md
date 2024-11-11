# Emailer

Welcome to **Emailer**! 🚀

Emailer is a fun and efficient email campaign manager that helps you create, manage, and track your email campaigns with ease. Whether you're sending newsletters, promotional emails, or any other type of email, Emailer has got you covered!

## Features

- **Create Campaigns**: Easily create email campaigns with customizable templates.
- **Upload CSV**: Upload a CSV file with recipient details and personalize your emails.
- **Track Progress**: Monitor the progress of your email campaigns in real-time.
- **Background Processing**: Emails are processed in the background, ensuring smooth and efficient delivery.

## Getting Started

To get started with Emailer, you'll need to set up some environment variables. Create a `.env` file in the root directory of your project and add the following variables:

```env
# SMTP Configuration
SMTP_GMAIL=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Groq API Key
GROQ_API_KEY=your_groq_api_key
```

## How to Run

1. Clone the repository:
    ```sh
    git clone https://github.com/vishan01/emailer.git
    cd emailer
    ```

2. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up the database:
    ```sh
    flask db upgrade
    ```

4. Start the application:
    ```sh
    flask run
    ```

5. Open your browser and navigate to `http://localhost:5000` to start using Emailer!

## Contributing

We welcome contributions! If you'd like to contribute, please fork the repository and submit a pull request.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

Happy emailing! 📧