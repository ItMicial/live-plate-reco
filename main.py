import cv2
import pytesseract
import mysql.connector
import re
from PIL import Image
import numpy as np
import os
import matplotlib
matplotlib.use('TkAgg')
pytesseract.pytesseract.tesseract_cmd ='D:/Tesseract-OCR/tesseract.exe'



#funkcja regexu tekstu
def contains_uppercases_numbers(text):
    # Definiowanie wzorca regex dla znaków specjalnych
    pattern = re.compile(r'^[A-Z0-9]+$')
    # szukanie duzych znakow i liczb oraz okreslenie dlugosci
    if pattern.search(text) and 8 > len(text) > 3:
        return True
    return False


# Tworzenie połączenia z bazą danych
conn = mysql.connector.connect(**config)

# Tworzenie kursora
cursor = conn.cursor()

# Uruchom kamerę
cap = cv2.VideoCapture(0)

# Sprawdź, czy kamera została pomyślnie uruchomiona
if not cap.isOpened():
    print("Nie można otworzyć kamery")
    exit()

# Utwórz plik tekstowy do zapisu numerów tablic rejestracyjnych
file = open("numery_tablic_rejestracyjnych.txt", "w")



while True:
    # Odczytaj klatkę z kamery
    ret, frame = cap.read()

    # Konwersja klatki na obraz w skali szarości
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Rozmycie obrazu w celu usunięcia szumu
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Wykrywanie krawędzi za pomocą algorytmu Canny'ego
    edges = cv2.Canny(blur, 100, 200)

    # Znalezienie konturów na obrazie krawędzi
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Pętla po znalezionych konturach
    for contour in contours:

        # Aproksymacja konturu za pomocą wielokąta
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)

        # Sprawdzenie, czy znaleziony kształt ma cztery boki
        if len(approx) == 4:
            # Wyodrębnienie regionu zainteresowania (ROI) tablicy rejestracyjnej
            x, y, w, h = cv2.boundingRect(approx)
            roi = frame[y:y+h, x:x+w]

            # Konwersja ROI do obrazu w skali szarości
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # Rozmycie obrazu ROI w celu usunięcia szumu
            blur_roi = cv2.GaussianBlur(gray_roi, (3, 3), 0)
            cv2.imwrite('screenshot.png', blur_roi)


            # Wykrywanie tekstu na obrazie ROI za pomocą PyTesseract
            text = pytesseract.image_to_string(blur_roi,)

            #Usuwanie spacji, białych znaków
            text = text.strip()
            text = re.sub(r"\s+", "", text)
           #print(text) testowanie
            # Sprawdzenie, czy wykryty tekst nie jest pusty
            if text and contains_uppercases_numbers(text):
                # Zapisanie wykrytego numeru tablicy rejestracyjnej do pliku tekstowego
                file.write(text + "\n")
                # Przygotowanie zapytania SQL
                query = "SELECT COUNT(*) FROM plate_reco WHERE nr_rejestracyjny = %s"
                # Wykonanie zapytania
                cursor.execute(query, (text,))
                # Pobieranie wyniku
                count = cursor.fetchone()[0]
                if (count > 0):
                    print(f"Zmienna '{text}' istnieje w tabeli Pojazdy w kolumnie nrRejestracyjny.")
                else:
                    print(f"Zmienna '{text}' nie istnieje w tabeli plate_reco w kolumnie nr_rejestracyjny.")
                    # Zapytanie użytkownika, czy dodać nowy numer rejestracyjny do bazy danych
                    add_to_db = input(
                        "Czy chcesz dodać ten numer rejestracyjny do bazy danych? (tak/nie): ").strip().lower()
                    if add_to_db == "tak":
                        # Dodanie nowego wpisu do bazy danych
                        insert_query = "INSERT INTO plate_reco (nr_rejestracyjny, czy_dozwolono) VALUES (%s, %s)"
                        cursor.execute(insert_query,(text, "NIE"))  # Domyślnie ustawiamy "NIE" w kolumnie czy_dozwolono
                        conn.commit()  # Zapisanie zmian w bazie danych
                        print(f"Numer rejestracyjny '{text}' został dodany do bazy danych.")
                    else:
                        print("Numer rejestracyjny nie został dodany do bazy danych.")


                # Wyświetlenie wykrytego tekstu
                print("Numer tablicy rejestracyjnej:", text)



                # Wyświetlenie obrazu ROI z prostokątem ograniczającym
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Wyświetlenie klatki z kamery z wykrytymi tablicami rejestracyjnymi
    cv2.imshow("Wykrywanie tablic rejestracyjnych", frame)

    # Naciśnięcie klawisza "q" kończy program
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Zamknięcie kursora i połączenia
cursor.close()
conn.close()

# Zamknięcie pliku tekstowego
file.close()

# Zwolnienie zasobów kamery
cap.release()

# Zniszczenie wszystkich okien
cv2.destroyAllWindows()





