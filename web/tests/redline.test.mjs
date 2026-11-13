// Run with: npm test   (Node's built-in test runner; Node 24 runs the .ts file directly)
import { test } from "node:test";
import assert from "node:assert/strict";
import { splitParts, wordDiff, compareSteps } from "../lib/redline.ts";

test("splits numbered parts but not section or fee numbers", () => {
  const t = "The Committee recommends that: 1. City Council in accordance with Section 71-11.1C authorize it. " +
    "2. City Council waive fees (Fee Ref. 61.06, 61.07). 3. City Council direct staff as per Item 2025.EX28.3.";
  const parts = splitParts(t);
  assert.deepEqual(parts.map((p) => p.n), [1, 2, 3]);
  assert.equal(parts[0].text, "City Council in accordance with Section 71-11.1C authorize it.");
  assert.equal(parts[1].text, "City Council waive fees (Fee Ref. 61.06, 61.07).");
  assert.equal(parts[2].text, "City Council direct staff as per Item 2025.EX28.3.");
});

test("no numbered parts gives an empty list", () => {
  assert.deepEqual(splitParts("City Council adopted the item."), []);
});

test("word diff keeps the original words and marks additions and removals", () => {
  const segs = wordDiff("utilize the procurement for any additional supply required.",
    "utilize the procurement for any increased quantity of deliverables.");
  assert.deepEqual(segs.filter((s) => s.op === "del").map((s) => s.text.trim()), ["additional supply required."]);
  assert.deepEqual(segs.filter((s) => s.op === "add").map((s) => s.text.trim()), ["increased quantity of deliverables."]);
  assert.equal(segs.filter((s) => s.op !== "del").map((s) => s.text).join(""),
    "utilize the procurement for any increased quantity of deliverables.");
});

test("curly vs straight apostrophes and spacing around / are not changes", () => {
  const r = compareSteps("recommends that: 1. Fund the City’s Plan / Village Fest now.",
    "adopted the following: 1. Fund the City's Plan/Village Fest now.");
  assert.deepEqual(r.map((c) => c.kind), ["same"]);
});

test("Council adds a part and renumbers the rest (like 2026.TE32.46 and 2026.EX31.2)", () => {
  const committee = "recommends that: 1. City Council authorize the street event on Church Street from June 19 to August 21. " +
    "2. City Council request an evaluation of the closure outcomes and risks. " +
    "3. City Council direct the City Manager to consolidate the requests to other governments.";
  const council = "adopted the following: 1. City Council authorize the street event on Church Street from June 19 to August 21. " +
    "2. City Council request an evaluation of the closure outcomes and risks. " +
    "3. City Council authorize the General Manager to cancel the temporary closure for public safety. " +
    "4. City Council direct the City Manager to consolidate the requests to other governments.";
  const r = compareSteps(committee, council);
  assert.deepEqual(r.map((c) => [c.kind, c.newN ?? null, c.oldN ?? null]),
    [["same", 1, 1], ["same", 2, 2], ["added", 3, null], ["same", 4, 3]]);
});

test("a part that is dropped shows as removed, and a rewritten part as changed", () => {
  const before = "recommends that: 1. City Council increase the budget by $1,060,000 from the reserve. " +
    "2. City Council request the Executive Director to consider examples from other cities and bring the by-law forward.";
  const after = "adopted the following: 1. City Council increase the budget by $1,060,000 from the reserve, as amended. " +
    "2. City Council ask the Province for an exemption to rent increases.";
  const r = compareSteps(before, after);
  assert.deepEqual(r.map((c) => c.kind), ["changed", "added", "removed"]);
  assert.equal(r[2].oldN, 2);
});
