# PRD — מערכת חיפוש והזמנת טיסות (FlightAdvisor)
**קורס:** הנדסת מערכות חלונות — פרויקט סיום, סמסטר ב' תשפ"ו
**גודל צוות:** זוג (2 מפתחים)
**סטטוס:** גרסה 0.1 — טרם התחלת קוד

---

## 1. רקע ומטרה

מערכת מבוזרת רב-שכבתית לחיפוש, בדיקה, והזמנה מדומה של טיסות, הכוללת:
- ממשק דסקטופ (PySide6)
- שרת Gateway
- שרת אפליקציה (FastAPI, CQRS/MVC)
- שירות RAG מקומי (Ollama ב-Docker) המשמש "יועץ טיסות"
- אחסון נתונים בענן עם גישת Event Sourcing (somee.com)
- אינטגרציה עם API חיצוני אמיתי לנתוני טיסות

המערכת מדמה תרחיש אמיתי של אתר/אפליקציית הזמנת טיסות (בסגנון Skyscanner/Kayak) בהיקף מצומצם המתאים לפרויקט קורס.

---

## 2. בחירת שירות חיצוני (סעיף 7 בדרישות)

**מומלץ:** AviationStack או Aerodatabox (שניהם מציעים free tier, נתוני טיסות אמיתיים/היסטוריים לפי מספר טיסה, שדה תעופה, או מסלול).
חלופה: OpenSky Network (חינמי לגמרי, ללא צורך ב-API key, אך פחות עשיר במידע מסחרי כמו מחירים).

**פעולה נדרשת מכם:** להירשם ל-API הנבחר, לקבל API key, ולוודא בקריאת בדיקה (curl/Postman) שהוא עובד — **לפני** תחילת הפיתוח.

> הערה: המידע על ה-APIs הללו עשוי להתעדכן — מומלץ לבדוק תיעוד עדכני ותנאי שימוש בזמן ההרשמה בפועל.

---

## 3. משתמשים ותפקידים

| תפקיד | הרשאות |
|---|---|
| Guest | חיפוש טיסות בלבד (ללא הזמנה) |
| Registered User | חיפוש, פרטים, גרפים, התייעצות AI, הזמנת טיסה |

**אימות (סעיף 2):** הרשמה + התחברות עם שם משתמש/אימייל וסיסמה (hash), טוקן JWT לניהול סשן מול ה-Gateway.

---

## 4. תהליכי משתמש (User Stories) — מיפוי לדרישות סעיף 3

### 4.1 חיפוש נתונים
**כמשתמש**, אני רוצה לחפש טיסות לפי עיר מוצא, עיר יעד, ותאריך, **כדי** לראות אפשרויות טיסה זמינות.
- קריאה ל-Gateway → App Server (Query side) → API חיצוני → סינון/עיבוד → תוצאות ל-UI
- שדות חיפוש: מוצא, יעד, תאריך, (אופציונלי: כיתת טיסה)

### 4.2 הצגת פרטים לתוצאה שנבחרה
**כמשתמש**, אני רוצה ללחוץ על טיסה מתוך תוצאות החיפוש ולראות פרטים מלאים (שעות, טרמינל, זמן טיסה, חברת תעופה, מחיר, עצירות).

### 4.3 הצגת נתונים בגרף/טבלה
**כמשתמש**, אני רוצה לראות השוואת מחירים/משכי טיסה בין התוצאות בגרף (QtCharts) וגם כטבלה ממויינת.
- דוגמה: Bar chart של מחיר לפי חברת תעופה, או Line chart של מחיר לפי תאריך (אם נשלפים מספר תאריכים).

### 4.4 התייעצות עם סוכן AI (RAG)
**כמשתמש**, אני רוצה לשאול "יועץ טיסות" שאלות כלליות בתחום (למשל: "מה ההבדל בין Economy ל-Premium Economy?", "כמה זמן מומלץ להגיע לפני טיסה בין-לאומית?", "מה זה Layover ומה הסיכונים בו?").
- מבוסס מסמכי ידע (FAQ/מדריכים) שנטענים ל-vector store, נשלפים ומוזנים ל-Ollama (RAG pipeline).

### 4.5 הזנת נתונים בנושא (הזמנה)
**כמשתמש**, אני רוצה להזין פרטי נוסע (שם, דרכון) ולבצע הזמנה מדומה לטיסה שבחרתי, ולקבל אישור הזמנה.
- זו פעולת **Command** ב-CQRS → יוצרת Event (`BookingCreated`) שנשמר ב-Event Store.

---

## 5. ארכיטקטורה

```
┌─────────────────┐      ┌──────────────────────┐      ┌───────────────────────┐
│   UI (PySide6)   │◄────►│   Gateway (FastAPI)   │◄────►│  App Server (FastAPI)  │
│  MVP + Microfront│      │  Auth, routing,       │      │  CQRS: Commands/Queries│
│  - SearchView    │      │  aggregation          │      │  MVC controllers       │
│  - DetailsView   │      └──────────┬────────────┘      └──────┬────────────────┘
│  - ChartView     │                 │                           │
│  - AdvisorView   │                 ▼                           ▼
│  - BookingView   │        ┌────────────────┐         ┌──────────────────┐
└──────────────────┘        │ External Flight │         │  Event Store /    │
                             │ API (Aviation-  │         │  Read DB          │
                             │ Stack/OpenSky)   │         │  (somee.com)      │
                             └────────────────┘         └────────┬──────────┘
                                                                   │
                                                          ┌────────▼─────────┐
                                                          │ Ollama + Docker   │
                                                          │ (RAG Advisor)     │
                                                          └───────────────────┘
```

**עקרונות מפתח:**
- **Gateway**: נקודת כניסה יחידה, מבצע authentication, ומנתב ל-App Server ולשירותים חיצוניים.
- **CQRS ב-App Server**: `commands/` (BookFlight, RegisterUser) נפרדים לגמרי מ-`queries/` (SearchFlights, GetFlightDetails, GetPriceStats).
- **Event Sourcing**: כל שינוי state (הרשמה, הזמנה) נשמר כ-Event ברצף; ה-Read Model נבנה ע"י Projection מה-Events.
- **Microfrontends ב-UI**: כל מסך (חיפוש/פרטים/גרף/יועץ/הזמנה) הוא מודול Qt עצמאי, מנוהל ע"י MainWindow לפי תבנית MVP (View פסיבי, Presenter מנהל לוגיקה, Model = קריאות ל-API).

---

## 6. Data Model (טיוטה ראשונית)

**Events (Event Store):**
- `UserRegistered { user_id, email, password_hash, created_at }`
- `FlightSearched { search_id, user_id, origin, destination, date, timestamp }` (אופציונלי, לצורכי אנליטיקס)
- `BookingCreated { booking_id, user_id, flight_id, passenger_name, passport_no, created_at }`
- `BookingCancelled { booking_id, cancelled_at }`

**Read Models (Query side, נבנים מה-Events + נתוני API חיצוני):**
- `FlightSummary { flight_id, airline, origin, destination, departure_time, arrival_time, price, stops }`
- `UserBookings { user_id, bookings: [BookingSummary] }`

---

## 7. API Endpoints ראשוניים (App Server)

| Method | Endpoint | סוג (CQRS) | תיאור |
|---|---|---|---|
| POST | `/auth/register` | Command | הרשמת משתמש |
| POST | `/auth/login` | Query | התחברות, מחזיר JWT |
| GET | `/flights/search?origin=&destination=&date=` | Query | חיפוש טיסות |
| GET | `/flights/{flight_id}` | Query | פרטי טיסה |
| GET | `/flights/stats?...` | Query | נתונים מצטברים לגרף |
| POST | `/bookings` | Command | יצירת הזמנה |
| GET | `/bookings/me` | Query | הזמנות המשתמש |
| POST | `/advisor/ask` | Query* | שאלה ליועץ ה-RAG |

*שאילתת ה-advisor אינה משנה state, לכן היא Query גם אם מבחינה טכנית "כותבת" ל-context זמני.

---

## 8. Non-Functional — תזכורת לדרישות מחייבות

- UI: PySide 6/6.5, MVP + Microfrontends
- גרפים: QtCharts
- App Server: FastAPI, MVC/CQRS
- אחסון: somee.com + Event Sourcing
- גישה לחוץ: Gateway pattern
- RAG: Ollama בתוך Docker
- תיעוד: PRD זה + מסמכי המשך בגרסת סוכני קוד (PIV) — **לוודא מול המרצה בדיוק מה נדרש בפורמט ה-PIV**
- קוד: GitHub Repo
- (לא חובה לזוג) Cloudinary

---

## 9. סדר פיתוח מוצע (Vertical Slices)

1. **Slice 0**: שלד ריפו, Docker-compose עם Ollama, חיבור בדיקה ל-API חיצוני (curl בלבד)
2. **Slice 1**: אימות משתמשים מקצה לקצה (UI login → Gateway → App Server → Event Store)
3. **Slice 2**: חיפוש טיסות מקצה לקצה (UI → Gateway → App Server Query → API חיצוני → תצוגה)
4. **Slice 3**: הצגת פרטים + גרף/טבלה
5. **Slice 4**: יועץ RAG (טעינת מסמכים, embeddings, שאילתה ל-Ollama)
6. **Slice 5**: הזמנה (Command side מלא + Event Sourcing)
7. **Slice 6**: ליטוש UX/UI, בדיקות, תיעוד סופי

---

## 10. פתוח / להחלטה

- [ ] בחירה סופית בין AviationStack / Aerodatabox / OpenSky
- [ ] הרשמה ל-somee.com ובדיקת חיבור DB
- [ ] בירור מדויק של מתודת "PIV" ו-"AIA" מול המרצה/חומרי הקורס
- [ ] רשימת מסמכי ידע ל-RAG (FAQ טיסות)
- [ ] מבנה תיקיות מדויק בריפו
