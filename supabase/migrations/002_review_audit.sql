-- Plain Council: review audit trail
--
-- When a signed-in clerk changes a sentence, the DATABASE records who and when
-- (not the browser, so it can't be faked). Clerks may fix the wording or change the
-- status, but never the evidence: the source quote, passage, stage or item.
-- Approving a sentence also sets the item's "checked on" date.

create or replace function stamp_review() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is not null then
    if new.quote_display is distinct from old.quote_display
       or new.passage_id is distinct from old.passage_id
       or new.stage      is distinct from old.stage
       or new.item_ref   is distinct from old.item_ref
       or new.ai_draft   is distinct from old.ai_draft then
      raise exception 'Reviewers can change the wording and status only, not the source evidence';
    end if;
    if new.status is distinct from old.status or new.text_en is distinct from old.text_en then
      new.reviewed_by := auth.uid();
      new.reviewed_at := now();
    end if;
  end if;
  if new.status = 'approved' and old.status is distinct from 'approved' then
    update items set checked_at = now() where ref = new.item_ref;
  end if;
  return new;
end $$;

create trigger claims_stamp_review
  before update on claims
  for each row execute function stamp_review();
