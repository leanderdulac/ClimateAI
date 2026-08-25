import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { KeyRound, Copy, Plus, Power, Shield } from 'lucide-react';

import { DashboardLayout } from '@/components/DashboardLayout';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  createPartner,
  generatePartnerKey,
  listPartnerKeys,
  listPartners,
  revokePartnerKey,
  updatePartner,
  type CreatedPartnerApiKey,
  type Partner,
  type PartnerApiKey,
} from '@/lib/api/partners';
import { useTranslation } from '@/hooks/useTranslation';

function partnerBaseUrl(): string {
  if (typeof window === 'undefined') {
    return '/api/v1/partner';
  }
  const { hostname, origin } = window.location;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000/api/v1/partner';
  }
  return `${origin}/api/v1/partner`;
}

export function PartnersPage() {
  const { t } = useTranslation();
  const catalogUrl = useMemo(() => `${partnerBaseUrl()}/catalog`, []);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [keys, setKeys] = useState<PartnerApiKey[]>([]);
  const [freshKey, setFreshKey] = useState<CreatedPartnerApiKey | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [email, setEmail] = useState('');
  const [keyName, setKeyName] = useState('Integração');

  const selected = partners.find((item) => item.id === selectedId) ?? null;

  const refresh = useCallback(async () => {
    setError(null);
    const rows = await listPartners();
    setPartners(rows);
    setSelectedId((current) => current ?? rows[0]?.id ?? null);
  }, []);

  useEffect(() => {
    refresh()
      .catch((exc: Error) => setError(exc.message))
      .finally(() => setLoading(false));
  }, [refresh]);

  useEffect(() => {
    if (!selectedId) {
      setKeys([]);
      return;
    }
    listPartnerKeys(selectedId).then(setKeys).catch((exc: Error) => setError(exc.message));
  }, [selectedId]);

  const copy = async (value: string) => {
    await navigator.clipboard.writeText(value);
  };

  const onCreatePartner = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const partner = await createPartner({
        name,
        slug: slug || undefined,
        contact_email: email || undefined,
      });
      setPartners((rows) => [partner, ...rows]);
      setSelectedId(partner.id);
      setName('');
      setSlug('');
      setEmail('');
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t('partners.error'));
    } finally {
      setSaving(false);
    }
  };

  const onGenerateKey = async () => {
    if (!selectedId) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const issued = await generatePartnerKey(selectedId, keyName || 'Integração');
      setFreshKey(issued);
      setKeys((rows) => [issued, ...rows]);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t('partners.error'));
    } finally {
      setSaving(false);
    }
  };

  const onRevoke = async (keyId: string) => {
    if (!selectedId) {
      return;
    }
    setSaving(true);
    try {
      await revokePartnerKey(selectedId, keyId);
      setKeys((rows) => rows.map((row) => (row.id === keyId ? { ...row, is_active: false } : row)));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t('partners.error'));
    } finally {
      setSaving(false);
    }
  };

  const onToggleApi = async () => {
    if (!selected) {
      return;
    }
    const updated = await updatePartner(selected.id, { api_enabled: !selected.api_enabled });
    setPartners((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
  };

  return (
    <DashboardLayout title={t('partners.title')} subtitle={t('partners.subtitle')}>
      <div className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Shield className="h-5 w-5" />
              {t('partners.catalog')}
            </CardTitle>
            <CardDescription>{t('partners.catalogHelp')}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <code className="flex-1 truncate rounded-md bg-muted px-3 py-2 text-sm">{catalogUrl}</code>
            <Button variant="outline" onClick={() => copy(catalogUrl)}>
              <Copy className="mr-2 h-4 w-4" />
              {t('partners.copy')}
            </Button>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <Card>
            <CardHeader>
              <CardTitle>{t('partners.newPartner')}</CardTitle>
              <CardDescription>{t('partners.newPartnerHelp')}</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-3" onSubmit={onCreatePartner}>
                <Input
                  required
                  placeholder={t('partners.name')}
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
                <Input
                  placeholder={t('partners.slug')}
                  value={slug}
                  onChange={(event) => setSlug(event.target.value)}
                />
                <Input
                  type="email"
                  placeholder={t('partners.email')}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
                <Button type="submit" disabled={saving || !name.trim()}>
                  <Plus className="mr-2 h-4 w-4" />
                  {t('partners.create')}
                </Button>
              </form>

              <div className="mt-6 space-y-2">
                <div className="text-sm font-medium">{t('partners.list')}</div>
                {loading && <p className="text-sm text-muted-foreground">{t('common.loading')}</p>}
                {!loading && partners.length === 0 && (
                  <p className="text-sm text-muted-foreground">{t('partners.empty')}</p>
                )}
                {partners.map((partner) => (
                  <button
                    key={partner.id}
                    type="button"
                    onClick={() => {
                      setSelectedId(partner.id);
                      setFreshKey(null);
                    }}
                    className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm ${
                      partner.id === selectedId ? 'border-primary bg-primary/5' : 'border-border'
                    }`}
                  >
                    <span>
                      <span className="font-medium">{partner.name}</span>
                      <span className="ml-2 text-muted-foreground">{partner.slug}</span>
                    </span>
                    <Badge variant={partner.api_enabled ? 'default' : 'secondary'}>
                      {partner.api_enabled ? t('partners.enabled') : t('partners.disabled')}
                    </Badge>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <KeyRound className="h-5 w-5" />
                {t('partners.keys')}
              </CardTitle>
              <CardDescription>
                {selected ? selected.name : t('partners.selectPartner')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {selected && (
                <>
                  <div className="flex flex-wrap gap-2">
                    <Input
                      value={keyName}
                      onChange={(event) => setKeyName(event.target.value)}
                      className="max-w-xs"
                    />
                    <Button onClick={onGenerateKey} disabled={saving || !selected.api_enabled}>
                      {t('partners.generate')}
                    </Button>
                    <Button variant="outline" onClick={onToggleApi} disabled={saving}>
                      <Power className="mr-2 h-4 w-4" />
                      {selected.api_enabled ? t('partners.disable') : t('partners.enable')}
                    </Button>
                  </div>

                  {freshKey && (
                    <Alert>
                      <AlertDescription className="space-y-2">
                        <p>{t('partners.secretOnce')}</p>
                        <div className="flex items-center gap-2">
                          <code className="flex-1 break-all rounded bg-muted px-2 py-1 text-xs">
                            {freshKey.secret_key}
                          </code>
                          <Button size="sm" variant="outline" onClick={() => copy(freshKey.secret_key)}>
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    {keys.map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm"
                      >
                        <div>
                          <div className="font-medium">{key.name || t('partners.unnamed')}</div>
                          <div className="text-muted-foreground">
                            {key.prefix}… · {key.is_active ? t('partners.active') : t('partners.revoked')}
                          </div>
                        </div>
                        {key.is_active && (
                          <Button variant="ghost" size="sm" onClick={() => onRevoke(key.id)}>
                            {t('partners.revoke')}
                          </Button>
                        )}
                      </div>
                    ))}
                    {keys.length === 0 && (
                      <p className="text-sm text-muted-foreground">{t('partners.noKeys')}</p>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default PartnersPage;
