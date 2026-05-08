class Numbers:
    """
    Utility class for number-related operations, specifically localized formatting.
    """

    @staticmethod
    def format_localized(value, lang='en', min_decimals=0, max_decimals=10, suffix=''):
        """
        Formats a number to a localized string.
        
        Args:
            value: The number to format (int, float, decimal).
            lang (str): Language 'es' or 'en'. Defaults to 'en'.
            min_decimals (int): Minimum fraction digits. Defaults to 0.
            max_decimals (int): Maximum fraction digits. Defaults to 10.
            suffix (str): Optional suffix (e.g. ' €'). Defaults to ''.
        
        Returns:
            str: The localized number as a string.
        """
        if value is None or value == '':
            return ''
        
        try:
            num = float(value)
        except (ValueError, TypeError):
            return str(value)

        # Determine how many decimals to show
        # We first format to max_decimals, then strip trailing zeros if they exceed min_decimals
        formatted_max = f"{num:,.{max_decimals}f}"
        
        if '.' in formatted_max:
            parts = formatted_max.split('.')
            integer_part = parts[0]
            decimal_part = parts[1]
            
            # Strip trailing zeros
            decimal_part = decimal_part.rstrip('0')
            
            # Ensure we have at least min_decimals
            if len(decimal_part) < min_decimals:
                decimal_part = (decimal_part + '0' * min_decimals)[:min_decimals]
            
            if decimal_part:
                formatted = f"{integer_part}.{decimal_part}"
            else:
                formatted = integer_part
        else:
            # No decimal point
            formatted = formatted_max

        # Apply localization
        if lang == 'es':
            # Spanish format: 1.234,56
            # Replace , with . (thousands) and . with , (decimal)
            # Using placeholder to avoid collision
            localized = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            # Default/English format: 1,234.56
            localized = formatted
            
        return f"{localized}{suffix}"
