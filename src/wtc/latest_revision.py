"""Current corrective batch, shared by clean builds and saved-scene migrations."""
from .paving_revision import apply as paving
from .lobby_revision import apply as lobby
from .facade_revision import apply as facade
from .wtc7_roof_revision import apply as roof7
from .crown_edge_revision import apply as crown_junction


def apply():
    for name,fn in (('paving',paving),('lobby',lobby),('facade',facade),('wtc7_roof',roof7),('crown_junction',crown_junction)):
        print('REVISION_START '+name,flush=True)
        fn()
        print('REVISION_DONE '+name,flush=True)
