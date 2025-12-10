"""
ПАРСЕР САЙТОВ КОМПАНИЙ
Ищет Telegram, WhatsApp и дополнительные контакты на сайтах компаний
"""

import re
import requests
from typing import Dict, List, Optional
from urllib.parse import urlparse
import time


class WebsiteParser:
    """Парсер сайтов для поиска контактов (Telegram, WhatsApp, etc.)"""
    
    def __init__(self, timeout: int = 10, user_agent: str = None):
        """
        Инициализация парсера
        
        Args:
            timeout: Таймаут запроса в секундах
            user_agent: User-Agent для запросов
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Регулярные выражения для поиска
        self.telegram_patterns = [
            r't\.me/([a-zA-Z0-9_]+)',  # t.me/username
            r'telegram\.me/([a-zA-Z0-9_]+)',  # telegram.me/username
            r'@([a-zA-Z0-9_]{5,32})',  # @username (минимум 5 символов)
            r'tg://resolve\?domain=([a-zA-Z0-9_]+)',  # tg://resolve
        ]
        
        self.whatsapp_patterns = [
            r'wa\.me/(\+?[0-9]{10,15})',  # wa.me/+79991234567
            r'api\.whatsapp\.com/send\?phone=(\+?[0-9]{10,15})',  # API ссылка
            r'whatsapp://send\?phone=(\+?[0-9]{10,15})',  # whatsapp:// протокол
            r'chat\.whatsapp\.com/([a-zA-Z0-9]+)',  # Групповой чат
        ]
        
        self.phone_patterns = [
            r'\+7[\s-]?\(?[0-9]{3}\)?[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}',  # +7
            r'8[\s-]?\(?[0-9]{3}\)?[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}',  # 8
        ]
        
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    def parse_website(self, url: str) -> Dict:
        """
        Парсит сайт и извлекает контакты
        
        Args:
            url: URL сайта для парсинга
            
        Returns:
            Словарь с найденными контактами
        """
        result = {
            'url': url,
            'success': False,
            'telegram': [],
            'whatsapp': [],
            'phones': [],
            'emails': [],
            'error': None
        }
        
        try:
            # Добавляем схему если её нет
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Делаем запрос
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Ищем Telegram
                result['telegram'] = self._find_telegram(html_content)
                
                # Ищем WhatsApp
                result['whatsapp'] = self._find_whatsapp(html_content)
                
                # Ищем телефоны
                result['phones'] = self._find_phones(html_content)
                
                # Ищем email
                result['emails'] = self._find_emails(html_content)
                
                # Успешно если нашли хоть что-то
                result['success'] = any([
                    result['telegram'],
                    result['whatsapp'],
                    result['phones'],
                    result['emails']
                ])
            else:
                result['error'] = f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            result['error'] = "Timeout"
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection error"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _find_telegram(self, html_content: str) -> List[str]:
        """Ищет Telegram контакты в HTML"""
        telegram_links = []
        
        for pattern in self.telegram_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Очищаем от лишнего
                cleaned = match.strip()
                
                # Фильтруем спам и типичные ложные срабатывания
                if self._is_valid_telegram(cleaned):
                    # Форматируем единообразно
                    if not cleaned.startswith('@'):
                        formatted = f"@{cleaned}"
                    else:
                        formatted = cleaned
                    
                    if formatted not in telegram_links:
                        telegram_links.append(formatted)
        
        return telegram_links[:5]  # Максимум 5 контактов
    
    def _find_whatsapp(self, html_content: str) -> List[str]:
        """Ищет WhatsApp контакты в HTML"""
        whatsapp_contacts = []
        
        for pattern in self.whatsapp_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                cleaned = match.strip()
                
                if self._is_valid_phone(cleaned):
                    # Форматируем телефон
                    formatted = self._format_phone(cleaned)
                    if formatted and formatted not in whatsapp_contacts:
                        whatsapp_contacts.append(formatted)
                elif 'chat.whatsapp.com' in pattern:
                    # Групповой чат
                    invite_link = f"https://chat.whatsapp.com/{cleaned}"
                    if invite_link not in whatsapp_contacts:
                        whatsapp_contacts.append(invite_link)
        
        return whatsapp_contacts[:3]  # Максимум 3 контакта
    
    def _find_phones(self, html_content: str) -> List[str]:
        """Ищет телефоны в HTML"""
        phones = []
        
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                cleaned = match.strip()
                
                if self._is_valid_phone(cleaned):
                    formatted = self._format_phone(cleaned)
                    if formatted and formatted not in phones:
                        phones.append(formatted)
        
        return phones[:5]  # Максимум 5 телефонов
    
    def _find_emails(self, html_content: str) -> List[str]:
        """Ищет email в HTML"""
        matches = re.findall(self.email_pattern, html_content)
        
        # Фильтруем спам и типичные ложные срабатывания
        emails = []
        for email in matches:
            email = email.lower().strip()
            
            if self._is_valid_email(email):
                if email not in emails:
                    emails.append(email)
        
        return emails[:5]  # Максимум 5 email
    
    def _is_valid_telegram(self, username: str) -> bool:
        """Проверяет валидность Telegram username"""
        if not username:
            return False
        
        # Удаляем @ если есть
        username = username.lstrip('@')
        
        # Минимум 5 символов
        if len(username) < 5:
            return False
        
        # Только буквы, цифры и подчеркивание
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False
        
        # Фильтруем типичные ложные срабатывания
        spam_keywords = [
            'example', 'test', 'demo', 'sample', 'placeholder',
            'username', 'user_name', 'your_name', 'contact',
            'undefined', 'null', 'none', 'admin'
        ]
        
        if username.lower() in spam_keywords:
            return False
        
        return True
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Проверяет валидность телефона"""
        if not phone:
            return False
        
        # Убираем все кроме цифр и +
        digits = re.sub(r'[^\d+]', '', phone)
        
        # Проверяем длину (для российских номеров)
        if len(digits) < 11:
            return False
        
        # Фильтруем "телефоны" которые явно не телефоны
        # (например, слишком много повторяющихся цифр)
        if len(set(digits)) < 4:  # Менее 4 уникальных цифр
            return False
        
        return True
    
    def _is_valid_email(self, email: str) -> bool:
        """Проверяет валидность email"""
        if not email:
            return False
        
        # Фильтруем типичные ложные срабатывания
        spam_domains = [
            'example.com', 'test.com', 'sample.com', 'domain.com',
            'email.com', 'mail.com', 'yoursite.com', 'website.com',
            'company.com', 'yourdomain.com'
        ]
        
        domain = email.split('@')[1] if '@' in email else ''
        if domain.lower() in spam_domains:
            return False
        
        spam_keywords = [
            'example', 'test', 'sample', 'demo', 'placeholder',
            'noreply', 'no-reply', 'donotreply', 'info@example'
        ]
        
        for keyword in spam_keywords:
            if keyword in email.lower():
                return False
        
        return True
    
    def _format_phone(self, phone: str) -> Optional[str]:
        """Форматирует телефон в единый формат"""
        # Убираем все кроме цифр и +
        digits = re.sub(r'[^\d+]', '', phone)
        
        # Для российских номеров
        if digits.startswith('8') and len(digits) == 11:
            digits = '+7' + digits[1:]
        elif digits.startswith('7') and len(digits) == 11:
            digits = '+' + digits
        
        # Проверяем что получился валидный номер
        if len(digits) >= 11:
            return digits
        
        return None
    
    def parse_multiple_websites(self, urls: List[str]) -> List[Dict]:
        """
        Парсит несколько сайтов
        
        Args:
            urls: Список URL для парсинга
            
        Returns:
            Список словарей с результатами
        """
        results = []
        
        for url in urls:
            result = self.parse_website(url)
            results.append(result)
            
            # Небольшая задержка между запросами
            time.sleep(0.5)
        
        return results


def main():
    """Тестовый запуск"""
    print("=" * 70)
    print("🔍 ТЕСТ ПАРСЕРА САЙТОВ")
    print("=" * 70)
    print()
    
    # Тестовые сайты
    test_urls = [
        'https://yandex.ru',
        'https://sber.ru',
        'https://vk.com',
    ]
    
    parser = WebsiteParser()
    
    for url in test_urls:
        print(f"Парсим: {url}")
        result = parser.parse_website(url)
        
        if result['success']:
            print(f"  ✓ Успешно")
            if result['telegram']:
                print(f"  📱 Telegram: {', '.join(result['telegram'])}")
            if result['whatsapp']:
                print(f"  💬 WhatsApp: {', '.join(result['whatsapp'])}")
            if result['phones']:
                print(f"  📞 Телефоны: {', '.join(result['phones'][:2])}...")
            if result['emails']:
                print(f"  📧 Email: {', '.join(result['emails'][:2])}...")
        else:
            print(f"  ✗ Ошибка: {result['error']}")
        
        print()


if __name__ == "__main__":
    main()

