from core import Engine, State, Uroboros
from core.psi_transition import make_psi_transition


def increment_psi(x, relations):
    value = x.get("x", 0)
    return {**x, "x": value + 1}, relations


engine = Engine(transition=make_psi_transition(increment_psi))

system = Uroboros(
    state=State(values={"x": 0}),
    engine=engine,
)

for _ in range(10):
    system = system.step()

print("Final state:", system.state.values)
