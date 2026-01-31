from diwire import Container, Lifetime

from delivery.http.factories import FastAPIFactory


class Registry:
    def register(self, container: Container) -> None:
        # Using string-based registration to avoid loading django-related code too early
        container.register(
            "FastAPIFactory",
            factory=lambda: container.resolve(FastAPIFactory),
            lifetime=Lifetime.SINGLETON,
        )
