from eralchemy2 import render_er

render_er(
    "postgresql://postgres:JEEVAN@localhost:5432/dataguard",
    "../docs/DataGuard_ER_Diagram.png"
)

print("ER Diagram Generated Successfully!")