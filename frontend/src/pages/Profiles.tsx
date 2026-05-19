import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, Loader2, Pencil, Plus, Star, Trash2, X } from 'lucide-react';

import PaperFrame from '@/design/PaperFrame';
import Masthead from '@/design/atoms/Masthead';
import RuleDouble from '@/design/atoms/RuleDouble';
import { INK, INK_SOFT, OXBLOOD, RULE, space, typeScale } from '@/design/tokens';
import {
  dangerBtn,
  errorStyle,
  ghostBtn,
  helperStyle,
  inputStyle,
  labelStyle,
  primaryBtn,
} from '@/design/forms';
import ProfileSwitcher from '@/components/ProfileSwitcher';
import { useProfiles } from '@/state/profileStore';

export default function Profiles() {
  const navigate = useNavigate();
  const {
    profiles,
    activeProfileId,
    loading,
    createProfile,
    renameProfile,
    setDefaultProfile,
    deleteProfile,
    setActiveProfile,
  } = useProfiles();

  const [newName, setNewName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftName, setDraftName] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!newName.trim()) return;
    setBusyId('__new__');
    try {
      const created = await createProfile(newName.trim());
      setNewName('');
      setActiveProfile(created.id);
    } catch (err: any) {
      setError(extractErrorMessage(err) ?? 'Could not create palate.');
    } finally {
      setBusyId(null);
    }
  };

  const startEdit = (id: string, currentName: string) => {
    setEditingId(id);
    setDraftName(currentName);
  };

  const saveEdit = async (id: string) => {
    if (!draftName.trim()) {
      setEditingId(null);
      return;
    }
    setBusyId(id);
    setError(null);
    try {
      await renameProfile(id, draftName.trim());
      setEditingId(null);
    } catch (err: any) {
      setError(extractErrorMessage(err) ?? 'Could not rename palate.');
    } finally {
      setBusyId(null);
    }
  };

  const promoteDefault = async (id: string) => {
    setBusyId(id);
    setError(null);
    try {
      await setDefaultProfile(id);
    } catch (err: any) {
      setError(extractErrorMessage(err) ?? 'Could not change default.');
    } finally {
      setBusyId(null);
    }
  };

  const removeProfile = async (id: string, name: string) => {
    if (profiles.length <= 1) {
      setError('You cannot delete your only palate.');
      return;
    }
    const ok = window.confirm(`Delete palate "${name}" and all its history? This cannot be undone.`);
    if (!ok) return;
    setBusyId(id);
    setError(null);
    try {
      await deleteProfile(id);
    } catch (err: any) {
      setError(extractErrorMessage(err) ?? 'Could not delete palate.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <PaperFrame>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Masthead />
        <ProfileSwitcher />
      </div>
      <RuleDouble />

      <div style={{ marginTop: space.lg, marginBottom: space.lg }}>
        <h1
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.h1,
            marginBottom: space.sm,
          }}
        >
          Palates
        </h1>
        <p
          style={{
            fontFamily: "'EB Garamond', serif",
            fontStyle: 'italic',
            fontSize: typeScale.body,
            color: INK_SOFT,
          }}
        >
          Each palate has its own CellarTracker history, inventory, and recommendation archive.
        </p>
      </div>

      {error && (
        <div style={{ ...errorStyle, color: OXBLOOD, marginBottom: space.md }}>{error}</div>
      )}

      <div style={{ display: 'grid', gap: space.sm, marginBottom: space.xl }}>
        {loading && profiles.length === 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: INK_SOFT }}>
            <Loader2 className="animate-spin" style={{ width: 16, height: 16 }} strokeWidth={1.5} />
            <span style={{ fontFamily: "'EB Garamond', serif", fontStyle: 'italic' }}>Loading palates…</span>
          </div>
        )}

        {profiles.map((p) => {
          const isEditing = editingId === p.id;
          const isActive = p.id === activeProfileId;
          const busy = busyId === p.id;

          return (
            <div
              key={p.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: space.sm,
                padding: `${space.sm} ${space.md}`,
                border: `1px solid ${isActive ? INK : RULE}`,
                background: isActive ? 'rgba(31,18,10,0.04)' : 'transparent',
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                {isEditing ? (
                  <input
                    autoFocus
                    value={draftName}
                    onChange={(e) => setDraftName(e.target.value)}
                    style={inputStyle}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveEdit(p.id);
                      if (e.key === 'Escape') setEditingId(null);
                    }}
                  />
                ) : (
                  <>
                    <div
                      style={{
                        fontFamily: "'EB Garamond', serif",
                        fontSize: typeScale.bodyLg,
                        color: INK,
                      }}
                    >
                      {p.name}
                    </div>
                    <div
                      style={{
                        fontFamily: "'Cormorant Garamond', serif",
                        fontStyle: 'italic',
                        fontSize: typeScale.micro,
                        letterSpacing: 1.5,
                        textTransform: 'uppercase',
                        color: INK_SOFT,
                      }}
                    >
                      {p.isDefault ? 'Default' : ''}
                      {p.isDefault && isActive ? ' · ' : ''}
                      {isActive ? 'Active' : ''}
                    </div>
                  </>
                )}
              </div>

              {isEditing ? (
                <>
                  <button type="button" onClick={() => saveEdit(p.id)} disabled={busy} style={primaryBtn} aria-label="Save name">
                    <Check style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                  </button>
                  <button type="button" onClick={() => setEditingId(null)} style={ghostBtn} aria-label="Cancel">
                    <X style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                  </button>
                </>
              ) : (
                <>
                  {!isActive && (
                    <button
                      type="button"
                      onClick={() => {
                        setActiveProfile(p.id);
                      }}
                      style={ghostBtn}
                    >
                      Activate
                    </button>
                  )}
                  {!p.isDefault && (
                    <button
                      type="button"
                      onClick={() => promoteDefault(p.id)}
                      disabled={busy}
                      style={ghostBtn}
                      aria-label="Make default"
                      title="Make default"
                    >
                      <Star style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => startEdit(p.id, p.name)}
                    style={ghostBtn}
                    aria-label="Rename"
                  >
                    <Pencil style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                  </button>
                  <button
                    type="button"
                    onClick={() => removeProfile(p.id, p.name)}
                    disabled={busy || profiles.length <= 1}
                    style={{ ...dangerBtn, opacity: profiles.length <= 1 ? 0.4 : 1 }}
                    aria-label="Delete"
                  >
                    <Trash2 style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                  </button>
                </>
              )}
            </div>
          );
        })}
      </div>

      <div>
        <div style={labelStyle}>Add a palate</div>
        <form onSubmit={handleCreate} style={{ display: 'flex', gap: space.sm, alignItems: 'stretch' }}>
          <input
            type="text"
            placeholder="e.g. Adventurous Mode"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            style={{ ...inputStyle, flex: 1 }}
            maxLength={64}
          />
          <button type="submit" disabled={!newName.trim() || busyId === '__new__'} style={primaryBtn}>
            {busyId === '__new__' ? (
              <Loader2 className="animate-spin" style={{ width: 14, height: 14 }} strokeWidth={1.5} />
            ) : (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Plus style={{ width: 14, height: 14 }} strokeWidth={1.5} />
                Create
              </span>
            )}
          </button>
        </form>
        <div style={helperStyle}>
          A new palate starts empty. Upload a CellarTracker export or seed it with named bottles from the{' '}
          <Link to="/profile" style={{ color: OXBLOOD }}>palate page</Link> after switching to it.
        </div>
      </div>

      <div style={{ marginTop: space.xl }}>
        <button type="button" onClick={() => navigate('/')} style={ghostBtn}>
          Back to recommendations
        </button>
      </div>
    </PaperFrame>
  );
}

function extractErrorMessage(err: any): string | null {
  if (!err) return null;
  if (typeof err === 'string') return err;
  const detail = err?.body?.detail ?? err?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return err?.message ?? null;
}
