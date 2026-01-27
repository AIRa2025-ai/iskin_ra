# modules/energy_calculator.py

def calculate_energy(number):
    """
    Вычисляет энергетическую вибрацию числа
    """
    if not isinstance(number, int) or number < 1:
        raise ValueError("Число должно быть целым и положительным")
    
    # Сводим число к единой вибрации
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    
    return number

def get_energy_description(energy_value):
    """
    Возвращает описание энергетической вибрации
    """
    descriptions = {
        1: "Энергия начала и лидерства",
        2: "Энергия гармонии и сотрудничества",
        3: "Энергия творчества и радости",
        4: "Энергия стабильности и порядка", 
        5: "Энергия свободы и изменений",
        6: "Энергия заботы и ответственности",
        7: "Энергия мудрости и анализа",
        8: "Энергия изобилия и власти",
        9: "Энергия завершения и мудрости"
    }
    
    return descriptions.get(energy_value, "Неизвестная вибрация")

# Пример использования
if __name__ == "__main__":
    test_number = 12345
    energy = calculate_energy(test_number)
    print(f"Энергия числа {test_number}: {energy} - {get_energy_description(energy)}")
