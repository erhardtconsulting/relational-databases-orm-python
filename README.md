# Notes Demo - Python ORM Lernprojekt

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue.svg)](https://www.postgresql.org/)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-purple.svg)](https://docs.astral.sh/uv/)

Ein umfassendes Lernprojekt für den Kurs **"Relationale Datenbanken"** der [Höheren Fachschule für Technik Mittelland](https://hftm.ch) zur praktischen Demonstration von Object Relational Mapping (ORM) mit modernen Python-Technologien.

🔗 **[Kurs-Website](https://relational-databases.erhardt.consulting/)**

## 📚 Lernziele

Dieses Projekt vermittelt Studierenden folgende Kernkonzepte:

- **Object Relational Mapping (ORM)** mit SQLAlchemy
- **FastAPI Fundamentals** - Asynchrone APIs, Dependency Injection, Auto-Dokumentation
- **Clean Architecture** - Separation of Concerns zwischen Model-, Schema-, Service- und Router-Schichten
- **Datenbankmanagement** - PostgreSQL Integration, Alembic Migrationen
- **Containerisierte Entwicklung** - Docker Compose für lokale Umgebung
- **Type-Safe Development** - Pydantic für sichere Datenvalidierung

## 🛠️ Technologie-Stack

### Backend
- **FastAPI** - Modernes, schnelles Web-Framework
- **Python 3.11+** - Moderne Python-Features und Performance
- **SQLAlchemy 2.0** - Object Relational Mapping
- **PostgreSQL 17** - Relationale Datenbank
- **Alembic** - Datenbankmigrationen

### Frontend
- **Jinja2** - Server-side HTML Templating
- **Bootstrap CSS** - Responsive Web Design

### Entwicklung & Testing
- **UV** - Blitzschnelles Package Management
- **Pytest** - Testing Framework
- **Docker Compose** - Lokale Entwicklungsumgebung

## 🚀 Installation und Einrichtung

### Voraussetzungen

- **Python 3.11** oder höher ([Python.org](https://www.python.org/))
- **UV** für Package Management ([Installation](https://docs.astral.sh/uv/))
- **Docker & Docker Compose** für die Datenbankumgebung
- **Git** für Versionskontrolle

### 1. Projekt klonen

```bash
git clone <repository-url>
cd notes-app
```

### 2. Datenbank starten

```bash
# PostgreSQL Datenbank mit Docker Compose starten
docker-compose -f docker-compose.db.yaml up -d

# Überprüfen, ob die Datenbank läuft
docker ps
```

### 3. Anwendung kompilieren und starten

```bash
# Dependencies mit UV installieren
uv sync

# Umgebungsvariablen konfigurieren
cp .env.example .env

# Anwendung starten
uv run python -m app.main

# Alternative: Mit uvicorn direkt
uv run uvicorn app.main:app --reload
```

### 4. Anwendung testen

- **Webanwendung:** http://localhost:8000
- **API Dokumentation:** http://localhost:8000/docs
- **Datenbank:** PostgreSQL auf localhost:5432
  - Database: `notesapp`
  - Username: `notesapp`
  - Password: `notesapp`

## 🏗️ Projektarchitektur

Das Projekt folgt einer **Layered Architecture** mit klarer Trennung der Verantwortlichkeiten:

```
app/
├── routers/                # 🌐 Presentation Layer
│   ├── web.py             # Web UI Endpoints
│   └── api.py             # REST API Endpoints
├── services/               # 💼 Business Logic Layer  
│   └── note_service.py     # Geschäftslogik & Datenbankoperationen
├── schemas/                # 📋 Data Transfer Objects
│   └── note.py             # Pydantic Schemas für Validierung
├── models/                 # 💾 Data Model Layer
│   └── note.py             # SQLAlchemy ORM Models
├── database.py             # 🔧 Datenbankverbindung
├── config.py               # ⚙️ Konfigurationsmanagement
└── main.py                 # 🚀 Application Factory
```

### 🔄 Datenfluss

```
HTTP Request → Router → Service → SQLAlchemy → Database
              ↓
         Schema/DTO ← Pydantic ← Model ← SQLAlchemy
```

## 💡 Kernkonzepte und Patterns

### 1. **ORM Model Definition**
```python
# SQLAlchemy Model (Datenbankrepräsentation)
class Note(Base):
    __tablename__ = "notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

### 2. **Schema Validation mit Pydantic**
```python
# Pydantic Schema für Datenvalidierung
class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)

class NoteResponse(BaseModel):
    id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)
```

### 3. **Service Layer Pattern**
```python
class NoteService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    async def create_note(self, note_data: NoteCreate) -> Note:
        note = Note(**note_data.model_dump())
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note
```

### 4. **Dependency Injection**
```python
@router.post("/notes", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    service: NoteService = Depends()
):
    return await service.create_note(note_data)
```

## 🧪 Testing

### Unit Tests ausführen
```bash
uv run pytest tests/unit -v
```

### Integration Tests ausführen
```bash
uv run pytest tests/integration -v
```

### Test Coverage Report
```bash
uv run pytest --cov=app --cov-report=html
# Report verfügbar unter: htmlcov/index.html
```

## 🎯 Pädagogische Übungen

### Grundübungen
1. **CRUD Operationen verstehen** - Analysiere die vollständigen Create/Read/Update/Delete Workflows
2. **Schema-Validierung erkunden** - Untersuche, wie Pydantic Eingabedaten validiert
3. **ORM-Queries schreiben** - Verstehe SQLAlchemy Query-Syntax und Filteroperationen

### Erweiterungsübungen
1. **Neue Entität hinzufügen** - Erstelle eine `Tag` Entität mit Many-to-Many Beziehung zu `Note`
2. **Erweiterte Validierung** - Füge Custom Validators in Pydantic Schemas hinzu
3. **Suchoption einbauen** - Implementiere Volltextsuche in Notizen
4. **Pagination hinzufügen** - Erweitere die API um Seitennummerierung

### Fortgeschrittene Übungen
1. **Asynchrone Datenbankoperationen** - Migriere zu async SQLAlchemy
2. **Caching implementieren** - Füge Redis-basiertes Caching hinzu
3. **Background Tasks** - Implementiere asynchrone Aufgaben mit Celery
4. **API Versionierung** - Erstelle versionierte API Endpoints

## 📁 Wichtige Dateien

| Datei | Zweck | Lernfokus |
|-------|-------|-----------|
| `models/note.py` | SQLAlchemy Model | ORM Mapping, Relationships |
| `schemas/note.py` | Pydantic Schemas | Datenvalidierung, Serialisierung |
| `services/note_service.py` | Business Logic | Service Pattern, Transaktionen |
| `routers/api.py` | REST API | FastAPI Routing, Dependencies |
| `routers/web.py` | Web UI | Template Rendering, Forms |
| `config.py` | Konfiguration | Settings Management |
| `alembic/` | Migrationen | Datenbankevolution |

## 🐳 Docker Entwicklungsumgebung

Das Projekt nutzt Docker Compose für eine konsistente Entwicklungsumgebung:

```yaml
# docker-compose.db.yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: notesapp
      POSTGRES_USER: notesapp
      POSTGRES_PASSWORD: notesapp
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### Nützliche Docker Befehle
```bash
# Datenbank starten
docker-compose -f docker-compose.db.yaml up -d

# Logs anzeigen
docker-compose -f docker-compose.db.yaml logs -f

# Datenbank stoppen
docker-compose -f docker-compose.db.yaml down

# Datenbank zurücksetzen
docker-compose -f docker-compose.db.yaml down -v
```

## 📖 Zusätzliche Ressourcen

### Dokumentation
- [FastAPI Dokumentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Pydantic Dokumentation](https://docs.pydantic.dev/)
- [UV Package Manager](https://docs.astral.sh/uv/)

### Lernmaterialien
- [Kurs: Relationale Datenbanken](https://relational-databases.erhardt.consulting/)
- [Python Async Programming](https://realpython.com/async-io-python/)
- [ORM Patterns in Python](https://www.sqlalchemy.org/library.html)

## 🤝 Beitragen

Dieses Projekt dient Bildungszwecken. Verbesserungsvorschläge und Erweiterungen sind willkommen:

1. Fork des Repositories erstellen
2. Feature Branch erstellen (`git checkout -b feature/neue-funktion`)
3. Änderungen committen (`git commit -am 'Füge neue Funktion hinzu'`)
4. Branch pushen (`git push origin feature/neue-funktion`)
5. Pull Request erstellen

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz und dient ausschliesslich Bildungszwecken im Rahmen des Kurses "Relationale Datenbanken" der Höheren Fachschule für Technik Mittelland.
