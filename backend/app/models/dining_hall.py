from sqlmodel import Field, SQLModel


class DiningHall(SQLModel, table=True):
    """Represents a physical dining hall at one of the 5C colleges."""

    __tablename__ = "dining_halls"

    id: str = Field(primary_key=True, max_length=20)
    name: str = Field(max_length=100)
    college: str = Field(max_length=20)
    vendor_type: str = Field(max_length=20)
    color: str | None = Field(default=None, max_length=7)
