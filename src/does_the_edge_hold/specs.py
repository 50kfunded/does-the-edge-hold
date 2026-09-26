"""Full-size contract price increments and dollar multipliers."""

from .ledger import ContractSpec


SPECS = {
    "NQ": ContractSpec("NQ", 20.0, 0.25),
    "ES": ContractSpec("ES", 50.0, 0.25),
    "YM": ContractSpec("YM", 5.0, 1.0),
    "GC": ContractSpec("GC", 100.0, 0.1),
    "CL": ContractSpec("CL", 1000.0, 0.01),
    "SYN": ContractSpec("SYN", 20.0, 0.25),
}
