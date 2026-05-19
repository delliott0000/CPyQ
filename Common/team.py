from .bases import IntIdentifiable
from .codecs import ContainerCodec, PrimitiveCodec, SerialisableCodec
from .company import Company
from .permissions import Permission

__all__ = ("Team",)


class Team(IntIdentifiable):
    codecs = {
        "name": PrimitiveCodec(str),
        "hierarchy_index": PrimitiveCodec(int),
        "company": SerialisableCodec(Company),
        "permissions": ContainerCodec(frozenset, SerialisableCodec(Permission)),
    }

    name: str
    hierarchy_index: int
    company: Company
    permissions: frozenset[Permission]

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index < other.hierarchy_index

    def __gt__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index > other.hierarchy_index

    def __le__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index <= other.hierarchy_index

    def __ge__(self, other):
        return self.__comparison_check__(other) or self.hierarchy_index >= other.hierarchy_index

    def __comparison_check__(self, other):
        if not isinstance(other, Team):
            return NotImplemented
        elif self.company != other.company:
            raise RuntimeError("Cannot compare two teams from different companies.")
        return False

    def has_permission(self, permission: Permission, /) -> bool:
        # fmt: off
        return (
            permission in self.permissions
            or
            any(
                perm.type == permission.type
                and
                perm.scope > permission.scope
                for perm in self.permissions
            )
        )
        # fmt: on
