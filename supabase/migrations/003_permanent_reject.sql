-- Plain Council: permanent rejection
--
-- "Rejected" can be undone (moved back to review). "Discarded" (shown as
-- "Permanently rejected") cannot: the row is kept so the project can report how
-- many AI sentences were corrected, but no one can change or publish it again.

alter type claim_status add value if not exists 'discarded';

-- Review history can now record every kind of action.
alter table reviews drop constraint if exists reviews_action_check;
alter table reviews add constraint reviews_action_check
  check (action in ('approve', 'edit', 'reject', 'restore', 'unpublish', 'discard'));

create or replace function stamp_review() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is not null then
    if old.status::text = 'discarded' then
      raise exception 'Permanently rejected sentences cannot be changed';
    end if;
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
