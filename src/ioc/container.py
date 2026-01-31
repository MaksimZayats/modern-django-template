from diwire import Container, Lifetime

from configs.logging import LoggingConfigurator
from infrastructure.frameworks.django.configurator import DjangoConfigurator
from infrastructure.frameworks.logfire.instrumentor import OpenTelemetryInstrumentor


class ContainerFactory:
    def __call__(
        self,
        *,
        configure_django: bool = True,
        configure_logging: bool = True,
        instrument_libraries: bool = True,
    ) -> Container:
        container = Container(autoregister_default_lifetime=Lifetime.SINGLETON)

        # It's required to configure Django before any registrations due to model imports
        if configure_django:
            self._configure_django(container)

        if configure_logging:
            self._configure_logging(container)

        if instrument_libraries:
            self._instrument_libraries(container)

        self._register(container)

        return container

    def _configure_django(self, container: Container) -> None:
        configurator = container.resolve(DjangoConfigurator)
        configurator.configure(django_settings_module="configs.django")

    def _configure_logging(self, container: Container) -> None:
        configurator = container.resolve(LoggingConfigurator)
        configurator.configure()

    def _instrument_libraries(self, container: Container) -> None:
        instrumentor = container.resolve(OpenTelemetryInstrumentor)
        instrumentor.instrument_libraries()

    def _register(self, container: Container) -> None:
        # Import registry functions here to avoid imports before setting up Django
        from ioc.registries import Registry  # noqa: PLC0415

        registry = container.resolve(Registry)
        registry.register(container)
