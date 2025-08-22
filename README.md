# Data Encryption System

A secure web-based application built with Django for encrypting and decrypting files and data.

## Features

- File Encryption/Decryption
- Data Text Encryption/Decryption
- Secure Key Generation
- Record System for Tracking Encryption Activities
- User-friendly Web Interface

## Project Structure

```
├── data_security_system/    # Main Django project directory
├── encryption/             # Main application directory
│   ├── templates/         # HTML templates
│   ├── models.py         # Database models
│   ├── views.py         # View logic
│   └── urls.py         # URL routing
├── media/               # Media storage
│   ├── encrypted_files/  # Storage for encrypted files
│   └── decrypted_files/ # Storage for decrypted files
├── templates/           # Global templates
└── manage.py           # Django management script
```

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Data-Encrption-System.git
cd Data-Encrption-System
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install django
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Access the application at `http://localhost:8000`

## Usage

1. **File Encryption/Decryption**
   - Upload files through the web interface
   - Choose encryption/decryption options
   - Download processed files

2. **Data Encryption**
   - Input text data through the web interface
   - Get encrypted/decrypted results

3. **Key Generation**
   - Generate secure encryption keys
   - Store and manage keys securely

## Security Features

- Secure file handling
- Encryption key management
- Protected file storage
- Access control

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please create an issue in the repository or contact the maintainers.