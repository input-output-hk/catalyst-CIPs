---
CIP: 36
Title: Catalyst Registration Transaction Metadata Format (Updated)
Authors:
  - Giacomo Pasini <giacomo.pasini@iohk.io>,
  - Kevin Hammond <kevin.hammond@iohk.io>,
  - Mark Stopka <mark.stopka@perlur.cloud>
  - Steven Johnson <steven.johnson@iohk.io>
Comments-URI: https://forum.cardano.org/t/cip-catalyst-registration-metadata-format/44038
Status: Proposed
Type: Standards
Created: 2021-12-06
License: CC-BY-4.0
---

## Abstract

Cardano uses a sidechain for its treasury system.
One needs to "register" to participate in a voting role on this sidechain by submitting a registration transaction on the mainnet chain.
This CIP details the registration and de-registration transaction format.
This is a revised version of the original CIP-15 and obsoletes it.

## Motivation

Cardano uses a sidechain for its treasury system ("Project Catalyst") and for other voting purposes.
One of the desirable properties of this sidechain is that even if its safety is compromised, it doesn't cause loss of funds on the main Cardano chain.
To achieve this, instead of using your wallet's recovery phrase on the sidechain, we need to use a brand new "voting key".

However, since 1 ADA = 1 vote, a user needs to associate their mainnet ADA to their new voting key.
This can be achieved through a registration or delegation transaction.
There are also two different voter roles:

- Self Registered Voters; or
- Representative Voters.

Self Registered Voters can elect to:

- Vote themselves; or
- Delegate their vote to one or more Registered Representatives.

Self Registered voters are eligible to receive voter rewards whether they vote personally or though representatives.

We therefore need a registration transaction that serves four purposes:

1. Allow one to unambiguously register for one of the roles and voting key, or to delegate their voting power.
2. Associates mainnet ADA to this voting key(s)
3. Declares a payment address to receive Catalyst rewards

This schema DOES differentiate delegations from direct registrations.
All Representatives are distinctly registered on-chain and will be treated equally.

## Specification

A registration transaction is a regular Cardano transaction with specific transaction metadata associated with it.
Other than the metadata the contents of the transaction are ignored.

Notably, there will be up to five entries inside the metadata map:

- A voters public key or non-empty array of delegations, as described below;
- A stake address for the network that this transaction is submitted to (to point to the Ada that is being delegated);
- A Shelley payment address (see [CIP-0019]) discriminated for the same network this transaction is submitted to, to receive rewards.
- A nonce that identifies that most recent registration.
- A non-negative integer that indicates the purpose of the vote.

### Voters Public Key

All Votes in project catalyst are signed with a private Ed25519 voting key.
The Catalyst Registration must be able to unambiguously determine what voter registrations are associated to signed votes.
Accordingly, each registration requires the Voters Public Key which is their 32 byte Public Key of their Private Ed25519 voting Key.
Only votes that can be validated against a properly registered Voters Public Key can be cast in a Project Catalyst Event.

The term governance should not be associated with these keys nor should these keys be associated with other vote or voting keys used in the ecosystem. When discussing these keys in a wider context they should be specified by such terminology as "CIP-36 vote keys" or "CIP-36 public vote keys".

#### Key Derivation

It is recommended where possible the Wallet employ path based key derivation to generate the voters key.
This is to avoid linking voting keys directly with Cardano spending keys.
The voting key derivation path must start with a specific segment:

`m / 61284' / 1815' / account' / chain' / purpose'`

- `61284'` : The registration metadata field key from this CIP.
  In an earlier draft this was 1694 but has been changed to avoid confusion with CIP-1694 which is unrelated to Catalyst.
- `1815'` : The year Ada Lovelace was born - Identifies this key as being for Cardano.
- `account'` : The voters account
- `chain'` : The chain on which the voter is registering.
- `purpose'` :  The purpose the voter is registering for.

If the wallet does not use path based key derivation it is recommended that:

- Voting keys not be valid for any purpose on Cardano other than catalyst voting.
- That different keys be used for different purposes.
  - The same wallet registering as either a Voter or Representatives should not use the same voting keys for each role.

### Delegation format

Only Voters can delegate to a Representative,  this is determined by the purpose of the registration.
When Delegating, the Voter assigns the ADA identified by their Stake Address to at least one Registered Representatives Voting Key.

Each delegation therefore contains:

- [The Representatives Public Vote Key](#voters-public-key): This is the Voter Key declared in a Representative Registration.  Only the Representative who registered that key can vote with it.
- The weight that is associated with this key: this is a 4-byte unsigned integer (CBOR major type 0, The weight may range from 0 to 2^32-1) that represents the relative weight of this delegation over the total weight of all delegations in the same registration transaction.

Notes:

- Delegations can ONLY be made to validly registered Representatives.
  - A Voter Registration that uses a registered Representatives Voting Key, but does not delegate will be INVALID regardless of whether it is witnessed or not.
- Any Delegation that is made to a Public Vote Key that is not a registered Representative will be ignored, and the weight assigned will have no effect.
- If there are no valid Representative Vote Keys in the Delegation, then the registration transaction that contains it is invalid and will not be used.
  - This prevents a voter from losing their voting power if their delegates de-register or change their voting keys.
- It is invalid for a Representative to delegate their voting power.
  - They MUST prove they control the voting key in their Representative Registration.

#### Tooling

Supporting tooling should clearly define and differentiate this as a unique key type, describing such keys as "CIP-36 vote keys". When utilizing Bech32 encoding the appropriate `cvote_sk` and `cvote_vk` prefixes should be used as described in [CIP-05](https://github.com/cardano-foundation/CIPs/tree/master/CIP-0005)

Examples of acceptable `keyType`s for supporting tools:

| `keyType` | Description |
| --------- | ----------- |
| `CIP36VoteSigningKey_ed25519` | Catalyst Vote Signing Key |
| `CIP36VoteExtendedSigningKey_ed25519` | Catalyst Vote Signing Key |
| `CIP36VoteVerificationKey_ed25519` | Catalyst Vote Verification Key |
| `CIP36VoteExtendedVerificationKey_ed25519` | Catalyst Vote Verification Key |

For hardware implementations:
| `keyType` | Description |
| --------- | ----------- |
| `CIP36VoteVerificationKey_ed25519` | Hardware Catalyst Vote Verification Key |
| `CIP36VoteHWSigningFile_ed25519` | Hardware Catalyst Vote Signing File |

The intention with this design is that if projects beyond Catalyst implement this specification they are able to add to themselves `keyType` **Description**s.

### Associating voting power with a voting key

This method has been used since Fund 2.

Recall: Cardano uses the UTXO model so to completely associate a wallet's balance with a voting key (i.e. including enterprise addresses), we would need to associate every payment key to a voting key individually.
Although there are attempts at this (see [CIP-0008]), the resulting data structure is excessive for on-chain metadata (which we want to keep small)

Given the above, we choose to associate staking credentials with voting keys.
The only supported staking credential is a staking key.
Since most Cardano wallets only use base addresses for Shelley wallet types, in most cases this should perfectly match the user's wallet.

#### Self Registered Voters

##### CIP-15 Format Registrations ONLY

If the voter only has CIP-15 Voter Registrations, their voting power is the sum total of all CIP-15 registrations that use the same [Voting Key](#voters-public-key).

Voter Rewards in this case will be distributed amongst the registrations, based on the amount of ADA they contributed to the total voting power.  This prevents a CIP-15 registration from stealing another voters voting reward.

CIP-15 Registration are deprecated, and once all tooling and community members have had sufficient time to move away from CIP-15 then CIP-15 format will be considered invalid.  At that time an update will be made to this specification to detail when CIP-15 format will cease to be recognized.

##### CIP-36 Format Registrations ONLY

It is a requirement that AT LEAST 1 CIP-36 Registration must attach a witness to prove it controls the [Voting Key](#voters-public-key).
If no CIP-36 Registrations prove ownership of the [Voting Key](#voters-public-key) then all CIP-36 registrations to that same [Voting Key](#voters-public-key) are INVALID.

Otherwise, all voting power associated with the same [Voting Key](#voters-public-key) will be accumulated.

Voter rewards will be accumulated and ONLY be paid to the CIP-36 registration that:

1. Proves control of the Vote Key with a witness; and
2. Proves control of the Stake Address with a witness; and
3. Has a valid Payment address; and
4. Has the highest nonce of any registration that has the same Vote Key; and
5. Has the Purpose set to 0.

These conditions are designed to inhibit shadow delegation.
Shadow delegation is where a voter registers with another voters voting key, and does not participate.
They do this simply to earn a voter reward, with no further effort on their behalf.
In this case, anyone who shadow delegates will deprive themselves of both their voting power and any voter reward they may have enjoyed from voting.
The voter who properly registered their voting key would be the sole beneficiary.
Any voter who wishes to accumulate multiple wallets worth of voting power into their own controlled voting key may still do so, and they will receive the full voter reward they were entitled to.

##### CIP-15 & CIP-36 Format Registrations

If the same Voting key appears in both CIP-15 and CIP-36 registrations and at least one CIP-36 registration has witnessed to [Voting Key](#voters-public-key), then the CIP-15 registrations will be treated as unwitnessed voting keys as in [CIP-36 Only](#cip-15-format-registrations-only).

Otherwise, the CIP-36 Registrations will be considered invalid, and the CIP-15 registrations will be treated as in [CIP-15 Only](#cip-15-format-registrations-only).

#### Representative Voters

Representatives MUST witness their voting key otherwise their representative voter registration will be INVALID.

A Representative accumulates ALL of their own voting power associated their Stake Address, plus the portion of ADA delegated to them by a Voter.  Representatives are a different class of voter, and may have different rules associated with their voting and conduct.  For Example:

- A Representative may have their votes de-anonymized at the end of a Catalyst Voting Event to prove their voting behaviour.
- May Earn different rewards, depending on their status (Public or Private Representative).
- May have different Voting Power Caps and Limits compared to a Self Registered Voter.
- Other differences associated with the role.
  - These differences are project Catalyst parameters and are outside of the scope of this document, except to highlight that Representatives are a different class and voter role than a self registered voter.

A Voter will earn to their reward address the voter reward their individual registration entitles them to.
Voter rewards can only be accumulated if multiple registrations use the same payment address.

#### Delegated Voters

A Delegated Voter has delegated all of their voting power to 1 or more registered Representative Voters.
It is not possible for a registered Representative Voter to delegate their vote.

The voting power that is associated with each delegated voting key is derived from the user's total voting power
as follows.

1. All voting keys are validated to correspond with a registered Representatives Voting key.
   1. Any voting key which does not correpond, and it's associated weight is ignored.
2. If there are no valid Representative Voting keys present in the Delegation Array then the registration transaction is invalid.
3. The total weight is then calculated as a sum of all the valid Representatives weights;
4. The voters's total voting power is calculated as a whole number of staked ADA (rounded down);
5. The voting power associated with each valid Representatives voting key in the delegation array is calculated as the weighted fraction of the total voting power (rounded down);
6. Any remaining voting power is assigned to the last voting key in the delegation array.

This ensures that the voter's total voting power is never accidentally reduced through poor choices of weights,
and that all voting powers are exact ADA.  It also ensures that ONLY registered Representatives can be Delegated to.
It is recommended that all voters should have a valid Self Registration before any Delegation is made.
This will ensure that should a delegation registration be invalidated because the delegates become invalid, the voter can still participate with their latest registration.

It is also possible to register in a sequence like so:

1. Self Registration
2. Delegate to Rep A
3. Delegate to Rep B

In this case, all Voting power will go the Rep B.
If they de-register or change their voting key, the voting power will fall back to Rep A,  and if that fails ultimately to the voters own Self Registration.
This enables preferential Delegation with a safety net fallback of direct voting.

### Generalized Registration Format

All Registrations follow the same generalized Format:

```json
61284: {
  // Voting Key or Delegation Array
  1: "0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663",
  // Stake Public Key
  2: "0xad4b948699193634a39dd56f779a2951a24779ad52aa7916f6912b8ec4702cee",
  // Payment Address
  3: "0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee47b60edc7772855324c85033c638364214cbfc6627889f81c4",
  // nonce
  4: 5479467,
  // Purpose
  5: 0
}

61285: {
  // Stake Public Key witness - ED25119 signature
  1: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007",
  // Voting Key witness - ED25119 signature
  2: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007"
}
```

Metadata is formatted with CBOR, and is strictly defined by the [CIP-0036-CDDL].

Different Roles and RegisSide effect oftration types will use different fields to unambiguously identify themselves.

The fields of the metadata are as follows:

- `61284` : Registration Metadata
  - `1` : Either :
    - Voting Key :
      `"0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663"`
      - A 32 Byte CBOR Byte String of the Raw Vote Public Key.
    - Delegation Array : `[["0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663", 1], ["0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee", 3]]`
      - A CBOR Array of Arrays.  Each inner array is:
        - A 32 Byte CBOR Byte String of the Raw Vote Public Key.
        - A 32 bit uint weight.
  - `2` : Stake Public Key : `"0xad4b948699193634a39dd56f779a2951a24779ad52aa7916f6912b8ec4702cee"`
    - A 32 Byte CBOR Byte String of the Raw Vote Public Key.
  - `3` : The Voter Reward Payment Address.
  `"0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee47b60edc7772855324c85033c638364214cbfc6627889f81c4"`
    - A 29 or 57 Byte CBOR Byte String of the Shelley Payment Address, as defined by [CIP-0019].
    - Note: CIP-15 format registration may also use a 29 Byte Stake Reward Address, but these are ineligible for rewards.
    CIP-36 registrations are invalid if they use a Stake Reward Address.
  - `4`: Nonce : `5479467`
    - The nonce is an unsigned integer (of CBOR major type 0) that should be monotonically rising across all transaction with the same staking key.
      The advised way to construct a nonce is to use the current slot number.
      This is a simple way to keep the nonce increasing without having to access the previous transaction data.
      Catalyst uses this to prioritize registrations.
      Registrations with higher Nonce values supersede registrations with lower nonce, for the same Staking Key.
  - `5`: Purpose : `0`
    - The Purpose is used to identify CIP-15 and CIP-36 registration format.
      CIP-15 does not include the Purpose, and any registration with a missing purpose will be validated according to CIP-15 rules.
      All CIP-36 registrations MUST include the Purpose.

- `61285` : Registration Witness
  - `1` : The Ed25519 Stake Address Signature of the `61284` CBOR Encoded Raw data. Encoded as a 64 Byte CBOR Byte String.
    `"0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007"`
    - Uses the Private Stake Key to sign, so this witness is verifiable with the Stake Public Key embedded in the metadata.
  - `2` : The Ed25519 Voting Key Signature of the `61284` CBOR Encoded Raw data. Encoded as a 64 Byte CBOR Byte String.
    `"0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007"`
    - Uses the Private Voting Key to sign, so this witness is verifiable with the Voting Key embedded in the metadata.
      - This field is NEVER present for CIP-15 registrations.
      - This field is ALWAYS present for CIP-36 registrations of Purpose 1 (Representative Voters).
      - This field is OPTIONALLY present for CIP-36 registrations of Purpose 0 (Self Voter) if and only if the wallet controls:
        - The Voter Private Key; and
        - The Voter Reward Payment Address.

All Roles and Types of Registrations can be unambiguously determined from this general format.

### CIP-0015 Voter Registration

CIP-15 Registrations are identified by the following characteristics:

- There is no Purpose Field.

ALL Registrations that lack a Purpose Field are by definition a CIP-15 Registration and MUST be validated by the following rules:

1. There is a single voters key.
   - Delegation Arrays are invalid in CIP-15.
2. The Stake Public Key validates against the `61285` Stake public key witness.
3. The Payment address is either a valid Shelley payment address OR a Stake Reward address.
   - If the payment Address is a Stake Reward address, then the registration allows voting,
     but will not be eligible for any voter rewards.
4. The Nonce is higher than any other registration txn with the same Stake Public Key.

#### Example

```json
61284: {
  // Voters Key - CBOR byte array
  1: "0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663",
  // stake_pub - CBOR byte array
  2: "0xad4b948699193634a39dd56f779a2951a24779ad52aa7916f6912b8ec4702cee",
  // payment_address - CBOR byte array
  3: "0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee47b60edc7772855324c85033c638364214cbfc6627889f81c4",
  // nonce
  4: 5479467
}
61285: {
  // Stake Public Key witness - ED25119 signature
  1: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007"
}
```

### CIP-0036 Voter Registration

CIP-36 Voter Registrations are identified by the following characteristics.

- There is a Purpose Field
- The Purpose Field = 0
- The Registration contains a Voters Key and not a Delegation Array.

ALL Registrations with a Purpose Field are by definition a CIP-36 Format Registrations.
Purpose 0 unambiguously identifies the registration as a Catalyst Voter Registration.
The single Voters Key identifies the registration as a Voters self registration and NOT a delegation.

It MUST be validated by the following rules:

1. There is a single voters key.
2. The Stake Public Key validates against the `61285` Stake public key witness.
3. The Payment address is a valid Shelley payment address.
4. The Nonce is higher than any other registration txn with the same Stake Public Key.
5. IF the Voting Key witness is present then it validates against the Voting Key.
6. That at least 1 registration with the same Voting Key is witnessed.

Note:  Only the Registration with the highest Nonce that is witnessed will be eligible to receive a voter reward to the Payment address.
But that payment address will receive the total voter reward payable based on the combined voting power of the voting key.

#### Example

```json
61284: {
  // Voting Key or Delegation Array
  1: "0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663",
  // Stake Public Key
  2: "0xad4b948699193634a39dd56f779a2951a24779ad52aa7916f6912b8ec4702cee",
  // Payment Address
  3: "0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee47b60edc7772855324c85033c638364214cbfc6627889f81c4",
  // nonce
  4: 5479467,
  // Purpose
  5: 0
}

61285: {
  // Stake Public Key witness - ED25119 signature
  1: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007",
  // Voting Key witness - ED25119 signature
  2: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007"
}
```

### CIP-0036 Representative Registration

CIP-36 Representative Registrations are identified by the following characteristics.

- There is a Purpose Field
- The Purpose Field = 1
- The Registration contains a Voters Key and not a Delegation Array.

ALL Registrations with a Purpose Field are by definition a CIP-36 Format Registrations.
Purpose 1 unambiguously identifies the registration as a Catalyst Representative Registration.
It is INVALID for a Representative to Delegate and so a Delegation Array is invalid for a Representative Registration.

It MUST be validated by the following rules:

1. There is a single voters key.
2. The Stake Public Key validates against the `61285` Stake public key witness.
3. The Payment address is a valid Shelley payment address.
4. The Nonce is higher than any other registration txn with the same Stake Public Key.
5. The Voting Key witness MUST be present and it validates against the Voting Key.

#### Example

```json
61284: {
  // Voting Key
  1: "0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663",
  // Stake Public Key
  2: "0xad4b948699193634a39dd56f779a2951a24779ad52aa7916f6912b8ec4702cee",
  // Payment Address
  3: "0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee47b60edc7772855324c85033c638364214cbfc6627889f81c4",
  // nonce
  4: 5479467,
  // Purpose
  5: 1
}

61285: {
  // Stake Public Key witness - ED25119 signature
  1: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007",
  // Voting Key witness - ED25119 signature
  2: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007"
}
```

### CIP-0036 Voter Delegation

CIP-36 Voter Delegations are identified by the following characteristics.

- There is a Purpose Field
- The Purpose Field = 0
- The Registration contains a Delegation Array and NOT a single Voter key.

ALL Registrations with a Purpose Field are by definition a CIP-36 Format Registrations.
Purpose 0 unambiguously identifies the registration as a Catalyst Voter Registration.
The Delegation Array identifies the registration as a Voters Delegation to Registered Representatives and not a self registration.

It MUST be validated by the following rules:

1. There is a Delegation Array, AND it contains at least 1 Valid Registered Representatives Vote key.
   - Invalid Registrations are excluded from the array when the registration is processed.
   - Registrations with a weight of 0 are excluded from the array when the registration is processed.
2. The Stake Public Key validates against the `61285` Stake public key witness.
3. The Payment address is a valid Shelley payment address.
4. The Nonce is higher than any other registration txn with the same Stake Public Key.
5. There is no Voting Key witness.

#### Example

```json
61284: {
  // Voting Key or Delegation Array
  1: [["0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663", 1], ["0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee", 3]],
  // Stake Public Key
  2: "0xad4b948699193634a39dd56f779a2951a24779ad52aa7916f6912b8ec4702cee",
  // Payment Address
  3: "0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee47b60edc7772855324c85033c638364214cbfc6627889f81c4",
  // nonce
  4: 5479467,
  // Purpose
  5: 0
}

61285: {
  // Stake Public Key witness - ED25119 signature
  1: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007",
  // Voting Key witness - ED25119 signature
  2: "0x8b508822ac89bacb1f9c3a3ef0dc62fd72a0bd3849e2381b17272b68a8f52ea8240dcc855f2264db29a8512bfcd522ab69b982cb011e5f43d0154e72f505f007"
}
```

In this example, Delegation to the voting key `0xa6a3c0447aeb9cc54cf6422ba32b294e5e1c3ef6d782f2acff4a70694c4d1663` will have relative weight 1 and delegation to the voting key `0x00588e8e1d18cba576a4d35758069fe94e53f638b6faf7c07b8abd2bc5c5cdee` relative weight 3 (for a total weight of 4).

Such a registration will assign 1/4 and 3/4 of the value in ADA to those keys respectively, with any remainder assigned to the second key.

### Registration Witness Calculations

`signData` = the CBOR representation of a map containing a single entry with key 61284 and the registration metadata map in the format above is formed.

The `signData` is hashed with the blake2b-256 hashing algorithm.

- `signDataHash` = `blake2b-256(signData)`

This hash is then signed using the Ed25519 signature algorithm and the appropriate private key. Either:

- The Stake Private Key, corresponding to the Stake Public Key; or
- The Vote Private Key, corresponding to the Vote Public Key;

The 64 byte Ed25519 Signature result is then encoded as a 64 byte CBOR Byte String in the appropriate field of the witness array.

Note: The witness is always signing the same Data and hash, the only thing that changes is the private key used.

### De-registration metadata format

De-registration cancels any previous registration made under this CIP for the same purpose.

Specifically:

- A de-registration resets the state of the stake credential on the voting chain like they were never registered before.
- A de-registration transaction is a regular Cardano transaction with a specific transaction metadata associated with it.

Notably, there should be three entries inside the metadata map (key 61286):

- The public key of the stake signing key being de-registered.
- A nonce that identifies that most recent de-registration. This is relative to the registration nonce, so the latest nonce be it a registration or de-registration prevails as the latest registration or de-registration.
- A non-negative integer that indicates the purpose of the vote.
  - 0 = Catalyst Voter De-registration.
  - 1 = Catalyst Representative De-registration.

Be aware, the de-registration metadata key is 61286, and not 61284 like it is used for a registration! The registration metadata format and specification is independent from the de-registration one, and may not be supported by all wallets/tools.

### Example - De-registration

```json
{
  61286: {
    // stake_pub - CBOR byte array
    2: "0x57758911253f6b31df2a87c10eb08a2c9b8450768cb8dd0d378d93f7c2e220f0",
    // nonce
    4: 74412400,
    // voting_purpose: 0 = Catalyst
    5: 0
  },
  61285: {
    // witness - ED25119 signature CBOR byte array
    1: "0xadb7c90955c348e432545276798478f02ee7c2be61fd44d22f9de22131d9bcf0b23eb413766b74b9e7ba740e71266467a5d35363411346972db9e7b710b00603"
  }
}
```

CBOR-Hex:
`A219EF66A301582057758911253F6B31DF2A87C10EB08A2C9B8450768CB8DD0D378D93F7C2E220F0021A046F7170030019EF65A1015840ADB7C90955C348E432545276798478F02EE7C2BE61FD44D22F9DE22131D9BCF0B23EB413766B74B9E7BA740E71266467A5D35363411346972DB9E7B710B00603`

The entries under keys 1, 2 and 3 represent the staking credential on the Cardano network, a nonce, and a voting purpose, respectively.
A deregistration with these metadata will be considered valid if the following conditions hold:

- The stake credentials is a stake public-key byte array (of CBOR major type 2)
- The nonce is an unsigned integer (of CBOR major type 0) that should be
  monotonically rising across all transactions with the same staking key.
  The advised way to construct a nonce is to use the current slot number.
  This is a simple way to keep the nonce increasing without having to access
  the previous transaction data.
- The voting_purpose is an unsigned integer (of CBOR major type 0)

The witness is produced identically to [The Registration Witness Calculation](#registration-witness-calculations)

### Metadata schema

See the [schema file][CIP-0036-CDDL]

### Test vector

See [test vector file](./test-vector.md)

## Changelog

Fund 3:

- added the `reward_address` inside the `key_registration` field.

Fund 4:

- added the `nonce` field to prevent replay attacks;
- changed the signature algorithm from one that signed `sign_data` directly
  to signing the Blake2b hash of `sign_data` to accommodate memory-constrained hardware wallet devices.

Fund 8:

- renamed the `voting_key` field to `delegations` and add support for splitting voting power across multiple vote keys.
- added the `voting_purpose` field to limit the scope of the delegations.
- rename the `staking_pub_key` field to `stake_credential` and `registration_signature` to `registration_witness` to allow for future credentials additions.

Fund 10:

- Replaced the `reward_address` field with `payment_address` field, keeping it at index 3. Stipulating that `payment_address` must be a Shelley payment address, otherwise voting reward payments will not be received.
  - **Note:** up to Catalyst's Fund 9, voting rewards were paid via MIR transfer to a stake address provided within the `reward_address` field. From Fund 10 onwards, a regular payment address must be provided in the `payment_address` field to receive voting rewards. This allows Catalyst to avoid MIR transfers and instead pay voting rewards via regular transactions.

Fund 11:

- Clearly distinguish between Voter Registration, Delegation and Representative Registration.
- Adds the `de-registration` metadata format.

## Copyright

This CIP is licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode)

[CIP-0008]: https://github.com/cardano-foundation/CIPs/tree/master/CIP-0008
[CIP-0019]: https://github.com/cardano-foundation/CIPs/tree/master/CIP-0019
[CIP-0036-CDDL]: ./schema.cddl
