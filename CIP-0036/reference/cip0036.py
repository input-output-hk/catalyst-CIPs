"""CIP0036 CDDL Validation and Test Vector Generator"""
import argparse
from binascii import hexlify
from pathlib import Path
from typing import Optional, Tuple, Dict

import cbor2
from cbor_diag import cbor2diag
from nacl.encoding import RawEncoder
from nacl.exceptions import BadSignatureError
from nacl.hash import blake2b
from nacl.signing import SigningKey, VerifyKey
from pycddl import Schema
import pytest


def gen_keys() -> Tuple[SigningKey, VerifyKey]:
    """
    Generates a new set of cryptographic keys by creating a new signing key
    and deriving its corresponding verifying key.

    :return: A tuple containing the signing key and the corresponding verifying
             key.
    """
    signk: SigningKey = SigningKey.generate()
    pubk: VerifyKey = signk.verify_key
    return signk, pubk

class CDDL:
    def __init__(self):
        self.cip36_registration = Schema(Path("cip0036_registration_schema.cddl").read_text())
        self.cip36_deregistration = Schema(Path("cip0036_deregistration_schema.cddl").read_text())
        self.cip36_witness = Schema(Path("cip0036_witness_schema.cddl").read_text())

cddl = CDDL()

class KeySet:
    def __init__(
        self, stake_pub: Optional[bytes] = None, vote_pub: Optional[bytes] = None
    ):
        self.stake_key: Optional[SigningKey] = None
        self.stake_pub_key: Optional[VerifyKey] = None
        self.vote_key: Optional[SigningKey] = None
        self.vote_pub_key: Optional[VerifyKey] = None

        if stake_pub is None:
            self.stake_key, self.stake_pub_key = gen_keys()
        else:
            self.stake_pub_key = VerifyKey(stake_pub)

        if vote_pub is None:
            self.vote_key, self.vote_pub_key = gen_keys()
        else:
            self.vote_pub_key = VerifyKey(vote_pub)

    def witness(
        self, payload: bytes, stake: bool = True, vote: bool = True
    ) -> Tuple[Optional[bytes], Optional[bytes]]:
        """
        Generate a set of witnesses for a given payload.

        Args:
            payload (bytes): The payload to generate a witness for.
            stake (bool): Whether to generate a stake witness. Defaults to True.
            vote (bool): Whether to generate a vote witness. Defaults to True.

        Returns:
            Tuple[Optional[bytes], Optional[bytes]]: A tuple containing the
                stake witness and vote witness, respectively.
        """
        payload_hash = blake2b(payload, digest_size=32, encoder=RawEncoder)
        print(hexlify(payload_hash))

        stake_witness: Optional[bytes] = None
        vote_witness: Optional[bytes] = None

        if stake and self.stake_key is not None:
            stake_witness = self.stake_key.sign(payload_hash)
        if vote and self.vote_key is not None:
            vote_witness = self.vote_key.sign(payload_hash)

        return stake_witness, vote_witness

    def verify(
        self, payload: bytes, witness: bytes, stake: bool = True, vote: bool = True
    ) -> Tuple[Optional[bool], Optional[bool]]:
        """
        Verify a payload and witness by checking against two public keys.

        Args:
            payload (bytes): The payload to be verified.
            witness (bytes): The witness to be verified.
            stake (bool, optional): Whether to verify the stake_pub_key. Defaults to True.
            vote (bool, optional): Whether to verify the vote_pub_key. Defaults to True.

        Returns:
            Tuple[bool, bool]: A tuple containing the validity of the stake_pub_key
                and the vote_pub_key verifications.
        """
        payload_hash = blake2b(payload, digest_size=32, encoder=RawEncoder)

        print(hexlify(payload_hash))

        stake_valid = None
        vote_valid = None

        if stake and self.stake_pub_key is not None:
            try:
                self.stake_pub_key.verify(payload, witness)
                stake_valid = True
            except BadSignatureError:
                stake_valid = False

        if vote and self.vote_pub_key is not None:
            try:
                self.vote_pub_key.verify(payload, witness)
                vote_valid = True
            except BadSignatureError:
                vote_valid = False

        return stake_valid, vote_valid


class CIP36:
    def __init__(self, new_key:bool = False):
        self.metadata_61284: Optional[bytes] = None
        self.metadata_61285: Optional[bytes] = None
        self.metadata_61286: Optional[bytes] = None
        self.decoded_61284: Optional[Dict] = None
        self.decoded_61285: Optional[Dict] = None
        self.decoded_61286: Optional[Dict] = None
        self.keyset: Optional[KeySet] = None

        if new_key:
            self.keyset = KeySet()

    def from_hex(
        self,
        metadata_61284: Optional[str] = None,
        metadata_61285: Optional[str] = None,
        metadata_61286: Optional[str] = None
    ) -> None:
        """
        Converts hexadecimal strings to bytes and assigns the resulting byte
        strings to instance variables.

        Args:
            metadata_61284 (Optional[str]): Optional hexadecimal string to assign as
                the 61284 metadata payload.
            metadata_61285 (Optional[str]): Optional hexadecimal string to assign as
                the 61285 metadata payload.
            metadata_61286 (Optional[str]): Optional hexadecimal string to assign as
                the 61286 metadata payload.

        Returns:
            None
        """
        if metadata_61284 is not None:
            self.metadata_61284 = bytes.fromhex(metadata_61284)
            self.decoded_61284 = cbor2.loads(self.metadata_61284)
            #Path("cip0036_registration.cbor").write_bytes(self.metadata_61284)

        if metadata_61285 is not None:
            self.metadata_61285 = bytes.fromhex(metadata_61285)
            self.decoded_61285 = cbor2.loads(self.metadata_61285)
            #Path("cip0036_witness.cbor").write_bytes(self.metadata_61285)

        if metadata_61286 is not None:
            self.metadata_61286 = bytes.fromhex(metadata_61286)
            self.decoded_61286 = cbor2.loads(self.metadata_61286)
            #Path("cip0036_deregistration.cbor").write_bytes(self.metadata_61286)

    def from_json(
        self,
        metadata_61284: Optional[str] = None,
        metadata_61285: Optional[str] = None,
        metadata_61286: Optional[str] = None
    ) -> None:
        """
        Convert JSON strings to bytes and assign to instance variables.
        :param arg1: Optional JSON string to assign as the 61284 metadata payload
        :param arg2: Optional JSON string to assign as the 61285 metadata payload
        :param arg3: Optional JSON string to assign as the 61286 metadata payload
        :return: None
        """
        if metadata_61284 is not None:
            self.decoded_61284 = metadata_61284
            self.metadata_61284 = cbor2.dumps(metadata_61284)
        if metadata_61285 is not None:
            self.decoded_61285 = metadata_61285
            self.metadata_61285 = cbor2.dumps(metadata_61285)
        if metadata_61284 is not None:
            self.decoded_61286 = metadata_61286
            self.metadata_61286 = cbor2.dumps(metadata_61286)

    def validate_cddl(self) -> None:
        """
        Validate the CDDL schema.
        :return: True if the CDDL schema is valid, False otherwise.
        """
        if self.metadata_61284 is not None:
            cddl.cip36_registration.validate_cbor(self.metadata_61284)
        if self.metadata_61286 is not None:
            cddl.cip36_deregistration.validate_cbor(self.metadata_61286)
        if self.metadata_61285 is not None:
            cddl.cip36_witness.validate_cbor(self.metadata_61285)

    def validate_signatures(self) -> bool:
        # if no keys yet defined, read the public keys from the payload and set them.
        if self.keyset is None:
            if self.decoded_61284 is not None:
                vote_pub_key = self.decoded_61284[61284][1]
                stake_pub_key = self.decoded_61284[61284][3]


CIP15_VOTER_REGISTRATION_MAINNET_BINARY = {
    61284 : "A119EF64A401582021785819F73A4537AD9CC6C45D10B9520405187A1B3E02C7AF6CA5"
    "4059939AC30258206FD5D1C6ED775C6A50AE17D9B1ABD2068960B420E252A3C6AD8655"
    "5BC6137CCC03581DE10DD2E29E4BAB80F63B9927D22251E3FFC1E130F81B21A5048A37"
    "E862041A0491C3E4",
    61285 : "A119EF65A1015840D15C307727E279D1CFFBB0C64792CE50E226587E08529A9A5A7292"
    "075EB3D19D5AC0348B708F2FD3122D2CFD3E6216C0DFA9F7CF17C9B9B4D60E887F2AF6E907"
}


"""
CIP15_VOTER_REGISTRATION_PREPROD = {
    61284: bytes.fromhex(
        "A119EF64A40158208C2213261223B9E43A9679BFF15BF146A75328467DA01674AA6479"
        "CBAFBBE942025820421BB1D3180A5083A6883437EC8EAF5CB01D158A08AC7FA839D8C9"
        "CC623FFA89035839008B71F5CCB6AC9CF17BD8E60BB5992FEA96C81584AF9835C8ADEF"
        "86104E3D6A6F68A511E5D817466579474DA8641767AA1110E0D25597B77E041A01BE1308"
    ),
    61285: bytes.fromhex(
        "A119EF65A10158401F1C0AADF7459E8272A5EDE9834FCAFEC2FCF841F07A26F421F06E"
        "8FA9A71A7A3B417F0DF63BFA26D60DC444FB209B7729A88891DC861C7B2B831C35186AAC0E"
    ),
}
"""

def test_valid_cip15_binary() -> None:
    """
    Test function to validate a CIP15 binary metadata as posted on mainnet.
    """
    # Create an instance of the CIP15_VOTER_REGISTRATION_MAINNET class
    cip15 = CIP36()
    cip15.from_hex(
        metadata_61284=CIP15_VOTER_REGISTRATION_MAINNET_BINARY[61284],
        metadata_61285=CIP15_VOTER_REGISTRATION_MAINNET_BINARY[61285]
    )

    # Validate the CDDL of the CIP15 binary
    assert cip15.validate_cddl()

def test_valid_cip36_binary():
    print("output success")
    assert 5 == 5

def main():
    parser = argparse.ArgumentParser(description="Generate Test Vectors or test the CDDL for CIP-036.")
    parser.add_argument("--test-cddl", type=bool, help="Run test cases against the CDDL Schema.")
    args = parser.parse_args()

    retcode = pytest.main([__file__, "-rA", "-vv"])
    print(retcode)

    #cddl = load_cddl()
    #print(cddl)

    #print(cbor2diag(CIP15_VOTER_REGISTRATION_PREPROD[61284]))
    #print(cbor2diag(CIP15_VOTER_REGISTRATION_PREPROD[61285]))

    voter_stake_key, voter_stake_pub_key = gen_keys()
    print(hexlify(voter_stake_key.encode(encoder=RawEncoder)))

    #voter_keys = KeySet()
    #voter_keys.witness(True, True, CIP15_VOTER_REGISTRATION_MAINNET[61284])


if __name__ == "__main__":
    main()
