import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Check, Copy, Download, FileText, Filter, LogOut, Minus, Plus, RefreshCw, Search, Trash2, Undo2 } from "lucide-react";

import { ApiError, api } from "./services/api";
import type {
  KtruCharacteristic,
  KtruGroup,
  KtruPosition,
  PostscriptTemplate,
  SelectedCharacteristic,
  SpecItem,
  TechnicalSpec,
  User,
} from "./types/domain";
import "./styles.css";

type Screen = "auth" | "pending" | "list" | "editor" | "preview";
type CharFilter = "all" | "required" | "optional" | "selected" | "no-unit";

const naturalCollator = new Intl.Collator("ru", {
  numeric: true,
  sensitivity: "base",
});

function sortByRefineValue(positions: KtruPosition[]) {
  return [...positions].sort((left, right) => {
    const valueCompare = naturalCollator.compare(left.refine_value || "", right.refine_value || "");
    if (valueCompare !== 0) return valueCompare;
    return naturalCollator.compare(left.code, right.code);
  });
}

function postscriptLines(spec: TechnicalSpec) {
  const templateLines = (spec.postscript_template_details || []).map((template) => template.text.trim()).filter(Boolean);
  const customLines = (spec.custom_postscript || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return [...templateLines, ...customLines];
}

function AuthScreen({ onLogin }: { onLogin: (user: User) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      if (mode === "register") {
        await api.register(email, password);
        setMessage("Заявка создана. Войти можно после одобрения администратором.");
        setMode("login");
        return;
      }
      const result = await api.login(email, password);
      onLogin(result.user);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Ошибка");
    }
  }

  return (
    <main className="auth-shell">
      <form className="auth-panel" onSubmit={submit}>
        <div>
          <p className="eyebrow">КТРУ MVP</p>
          <h1>Конфигуратор технического задания</h1>
        </div>
        <div className="tabs">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            Вход
          </button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
            Регистрация
          </button>
        </div>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
        </label>
        <label>
          Пароль
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required />
        </label>
        {message && <div className="notice">{message}</div>}
        <button className="primary" type="submit">
          {mode === "login" ? "Войти" : "Отправить заявку"}
        </button>
      </form>
    </main>
  );
}

function AppHeader({ user, onLogout }: { user: User; onLogout: () => void }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Конфигуратор ТЗ по КТРУ</p>
        <h1>Рабочий кабинет</h1>
      </div>
      <div className="userline">
        <span>{user.email}</span>
        <button className="ghost icon-text" onClick={onLogout}>
          <LogOut size={16} /> Выйти
        </button>
      </div>
    </header>
  );
}

function SpecList({
  specs,
  search,
  setSearch,
  onCreate,
  onOpen,
  onCopy,
  onDelete,
  onRefresh,
}: {
  specs: TechnicalSpec[];
  search: string;
  setSearch: (value: string) => void;
  onCreate: (title: string) => void;
  onOpen: (spec: TechnicalSpec) => void;
  onCopy: (id: number) => void;
  onDelete: (id: number) => void;
  onRefresh: () => void;
}) {
  const [title, setTitle] = useState("");

  return (
    <section className="workspace">
      <div className="toolbar">
        <label className="searchbox">
          <Search size={16} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Поиск ТЗ" />
        </label>
        <button className="ghost icon" onClick={onRefresh} title="Обновить">
          <RefreshCw size={18} />
        </button>
      </div>
      <form
        className="create-row"
        onSubmit={(event) => {
          event.preventDefault();
          onCreate(title.trim() || `Новое ТЗ ${new Date().toLocaleString("ru-RU")}`);
          setTitle("");
        }}
      >
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название черновика" />
        <button className="primary icon-text" type="submit">
          <Plus size={18} /> Создать
        </button>
      </form>
      <div className="table">
        <div className="table-head spec-grid">
          <span>Название</span>
          <span>Статус</span>
          <span>Обновлено</span>
          <span>Действия</span>
        </div>
        {specs.map((spec) => (
          <div className="table-row spec-grid" key={spec.id}>
            <strong>{spec.title}</strong>
            <span>{spec.status === "draft" ? "Черновик" : "Сохранено"}</span>
            <span>{new Date(spec.updated_at).toLocaleString("ru-RU")}</span>
            <div className="actions">
              <button className="ghost icon-text" onClick={() => onOpen(spec)}>
                <FileText size={16} /> Открыть
              </button>
              <button className="ghost icon" onClick={() => onCopy(spec.id)} title="Копировать">
                <Copy size={16} />
              </button>
              <button className="danger icon" onClick={() => onDelete(spec.id)} title="Удалить">
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
        {!specs.length && <div className="empty">Пока нет технических заданий.</div>}
      </div>
    </section>
  );
}

function CharacteristicPicker({
  characteristics,
  selected,
  onChange,
}: {
  characteristics: KtruCharacteristic[];
  selected: Record<number, SelectedCharacteristic>;
  onChange: (next: Record<number, SelectedCharacteristic>) => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<CharFilter>("all");

  function toggleValue(characteristic: KtruCharacteristic, value: string) {
    const current = selected[characteristic.id] || { characteristic_id: characteristic.id, selected_values: [], is_active: true };
    if (!current.is_active) return;
    const exists = current.selected_values.includes(value);
    const nextValues = characteristic.is_multiple_choice
      ? exists
        ? current.selected_values.filter((item) => item !== value)
        : [...current.selected_values, value]
      : exists
        ? []
        : [value];
    onChange({ ...selected, [characteristic.id]: { ...current, selected_values: nextValues } });
  }

  function setActive(characteristic: KtruCharacteristic, isActive: boolean) {
    if (characteristic.is_required) return;
    const current = selected[characteristic.id] || { characteristic_id: characteristic.id, selected_values: [], is_active: true };
    onChange({
      ...selected,
      [characteristic.id]: {
        ...current,
        selected_values: isActive ? current.selected_values : [],
        is_active: isActive,
      },
    });
  }

  const visible = characteristics.filter((characteristic) => {
    const current = selected[characteristic.id];
    const hasValue = Boolean(current?.selected_values.length);
    const active = current?.is_active !== false;
    const matchesQuery = `${characteristic.name} ${characteristic.unit_name}`.toLowerCase().includes(query.toLowerCase());
    if (!matchesQuery) return false;
    if (filter === "required") return characteristic.is_required;
    if (filter === "optional") return !characteristic.is_required;
    if (filter === "selected") return active && hasValue;
    if (filter === "no-unit") return !characteristic.unit_name;
    return true;
  });

  const groups = [
    ["Обязательные", visible.filter((item) => item.is_required)],
    ["Необязательные", visible.filter((item) => !item.is_required)],
  ] as const;

  const filters: Array<[CharFilter, string]> = [
    ["all", `Все (${characteristics.length})`],
    ["required", `Обязательные (${characteristics.filter((item) => item.is_required).length})`],
    ["optional", `Необязательные (${characteristics.filter((item) => !item.is_required).length})`],
    ["selected", `Выбранные (${Object.values(selected).filter((item) => item.is_active !== false && item.selected_values.length).length})`],
    ["no-unit", `Без ед. изм. (${characteristics.filter((item) => !item.unit_name).length})`],
  ];

  return (
    <div className="characteristics">
      <div className="char-tools">
        <label className="searchbox compact">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Поиск по списку характеристик" />
        </label>
        <div className="segmented" aria-label="Фильтр характеристик">
          {filters.map(([key, label]) => (
            <button type="button" key={key} className={filter === key ? "active" : ""} onClick={() => setFilter(key)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {groups.map(([title, items]) => (
        <section key={title} className="char-section">
          <h3>
            <Filter size={16} /> {title}
          </h3>
          {items.map((characteristic) => {
            const current = selected[characteristic.id] || {
              characteristic_id: characteristic.id,
              selected_values: [],
              is_active: true,
            };
            return (
              <div className={current.is_active ? "char-card" : "char-card disabled"} key={characteristic.id}>
                <div className="char-title">
                  <div>
                    <strong>{characteristic.name}</strong>
                    <span>{characteristic.unit_name || "Единица измерения не указана"}</span>
                  </div>
                  {!characteristic.is_required && (
                    <button
                      className="ghost icon"
                      onClick={() => setActive(characteristic, !current.is_active)}
                      title={current.is_active ? "Исключить характеристику" : "Вернуть характеристику"}
                    >
                      {current.is_active ? <Minus size={16} /> : <Undo2 size={16} />}
                    </button>
                  )}
                </div>
                <div className="chips">
                  {characteristic.values.map((value) => (
                    <button
                      type="button"
                      key={value.id}
                      disabled={!current.is_active}
                      className={current.selected_values.includes(value.value) ? "chip selected" : "chip"}
                      onClick={() => toggleValue(characteristic, value.value)}
                    >
                      {value.value}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
          {!items.length && <p className="muted">Нет характеристик под выбранный фильтр.</p>}
        </section>
      ))}
    </div>
  );
}

function PostscriptPanel({
  spec,
  templates,
  onSave,
}: {
  spec: TechnicalSpec;
  templates: PostscriptTemplate[];
  onSave: (payload: { postscript_templates: number[]; custom_postscript: string }) => Promise<void>;
}) {
  const [selectedIds, setSelectedIds] = useState<number[]>(spec.postscript_templates || []);
  const [customText, setCustomText] = useState(spec.custom_postscript || "");
  const [message, setMessage] = useState("");

  useEffect(() => {
    setSelectedIds(spec.postscript_templates || []);
    setCustomText(spec.custom_postscript || "");
  }, [spec.id, spec.postscript_templates, spec.custom_postscript]);

  function toggleTemplate(id: number) {
    setSelectedIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  async function save() {
    setMessage("");
    await onSave({ postscript_templates: selectedIds, custom_postscript: customText });
    setMessage("Приписки сохранены.");
  }

  return (
    <section className="postscript-panel">
      <div className="section-title">
        <h3>Приписки</h3>
        <button className="secondary" type="button" onClick={save}>
          Сохранить
        </button>
      </div>
      {templates.length > 0 ? (
        <div className="postscript-list">
          {templates.map((template) => (
            <label className="check-row" key={template.id}>
              <input type="checkbox" checked={selectedIds.includes(template.id)} onChange={() => toggleTemplate(template.id)} />
              <span>
                <strong>{template.name}</strong>
                <em>{template.text}</em>
              </span>
            </label>
          ))}
        </div>
      ) : (
        <p className="muted">Активных шаблонов пока нет. Их можно добавить в админке.</p>
      )}
      <label>
        Свой текст приписок
        <textarea value={customText} onChange={(event) => setCustomText(event.target.value)} rows={4} placeholder="Каждая строка станет отдельной припиской" />
      </label>
      {message && <div className="notice compact-notice">{message}</div>}
    </section>
  );
}

function Editor({
  spec,
  groups,
  postscriptTemplates,
  onBack,
  onPreview,
  onReload,
}: {
  spec: TechnicalSpec;
  groups: KtruGroup[];
  postscriptTemplates: PostscriptTemplate[];
  onBack: () => void;
  onPreview: (spec: TechnicalSpec) => void;
  onReload: (id: number) => Promise<TechnicalSpec>;
}) {
  const [groupId, setGroupId] = useState<number>(groups[0]?.id || 0);
  const [refineValue, setRefineValue] = useState("");
  const [groupPositions, setGroupPositions] = useState<KtruPosition[]>([]);
  const [position, setPosition] = useState<KtruPosition | null>(null);
  const [editingItem, setEditingItem] = useState<SpecItem | null>(null);
  const [ambiguousPositions, setAmbiguousPositions] = useState<KtruPosition[]>([]);
  const [selected, setSelected] = useState<Record<number, SelectedCharacteristic>>({});
  const [quantity, setQuantity] = useState("1");
  const [message, setMessage] = useState("");

  const currentGroup = groups.find((group) => group.id === groupId);
  useEffect(() => {
    if (!groupId) return;
    api
      .positionsByGroup(groupId)
      .then((positions) => {
        const sortedPositions = sortByRefineValue(positions);
        setGroupPositions(sortedPositions);
        if (editingItem) return;
        setRefineValue(sortedPositions[0]?.refine_value || "");
        setPosition(null);
        setAmbiguousPositions([]);
        setSelected({});
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "Не удалось загрузить значения"));
  }, [groupId, editingItem]);

  const requiredDone = useMemo(() => {
    const required = position?.characteristics?.filter((item) => item.is_required) || [];
    return required.every((item) => selected[item.id]?.is_active !== false && selected[item.id]?.selected_values.length);
  }, [position, selected]);

  async function preparePosition(positionId: number) {
    const detail = await api.position(positionId);
    setPosition(detail);
    const initial: Record<number, SelectedCharacteristic> = {};
    detail.characteristics?.forEach((char) => {
      initial[char.id] = { characteristic_id: char.id, selected_values: [], is_active: true };
    });
    setSelected(initial);
  }

  function resetEditorForm() {
    setEditingItem(null);
    setPosition(null);
    setSelected({});
    setAmbiguousPositions([]);
    setRefineValue(groupPositions[0]?.refine_value || "");
    setQuantity("1");
  }

  async function editExistingItem(item: SpecItem) {
    setMessage("");
    setAmbiguousPositions([]);
    setEditingItem(item);
    setGroupId(item.ktru_position_detail.group);
    setRefineValue(item.ktru_position_detail.refine_value);
    setQuantity(String(item.quantity).replace(/\.00$/, ""));
    const detail = await api.position(item.ktru_position);
    setPosition(detail);
    const nextSelected: Record<number, SelectedCharacteristic> = {};
    detail.characteristics?.forEach((char) => {
      const saved = item.selected_characteristics.find((entry) => entry.ktru_characteristic === char.id);
      nextSelected[char.id] = {
        characteristic_id: char.id,
        selected_values: saved?.selected_values || [],
        is_active: saved ? saved.is_active : !char.is_required,
      };
    });
    setSelected(nextSelected);
  }

  async function deleteExistingItem(item: SpecItem) {
    setMessage("");
    await api.deleteItem(spec.id, item.id);
    await onReload(spec.id);
    if (editingItem?.id === item.id) resetEditorForm();
    setMessage("Позиция удалена.");
  }

  async function savePostscriptSettings(payload: { postscript_templates: number[]; custom_postscript: string }) {
    await api.updateSpec(spec.id, payload);
    await onReload(spec.id);
  }

  async function resolve() {
    setMessage("");
    setAmbiguousPositions([]);
    setPosition(null);
    try {
      const resolved = await api.resolveRefined(groupId, refineValue);
      await preparePosition(resolved.id);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409 && Array.isArray(error.data?.positions)) {
        setAmbiguousPositions(error.data.positions);
        setMessage("Найдено несколько уточненных КТРУ. Выберите нужную позицию из списка.");
        return;
      }
      setMessage(error instanceof Error ? error.message : "Не удалось определить КТРУ");
    }
  }

  async function saveItem() {
    if (!position || !requiredDone) return;
    setMessage("");
    const payload = {
      position_number: editingItem?.position_number || spec.items.length + 1,
      ktru_position: position.id,
      object_name: position.name,
      quantity,
      unit_name: position.unit_name || "шт.",
      display_order: editingItem?.display_order || spec.items.length + 1,
      characteristics: Object.values(selected),
    };
    try {
      if (editingItem) {
        await api.updateItem(spec.id, editingItem.id, payload);
      } else {
        await api.addItem(spec.id, payload);
      }
      const updated = await onReload(spec.id);
      const wasEditing = Boolean(editingItem);
      resetEditorForm();
      setMessage(wasEditing ? "Позиция обновлена." : "Позиция добавлена.");
      if (!wasEditing) onPreview(updated);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось сохранить позицию");
    }
  }

  return (
    <section className="workspace editor-grid">
      <div className="side-panel">
        <button className="ghost" onClick={onBack}>
          Назад к списку
        </button>
        <h2>{spec.title}</h2>
        <div className="item-list">
          {spec.items.map((item) => (
            <div key={item.id} className={editingItem?.id === item.id ? "mini-item active" : "mini-item"}>
              <button className="mini-main" onClick={() => editExistingItem(item)}>
                <strong>{item.object_name}</strong>
                <span>{item.ktru_position_detail.code}</span>
              </button>
              <div className="mini-actions">
                <button className="ghost icon-text" onClick={() => editExistingItem(item)}>
                  Редактировать
                </button>
                <button className="danger icon" onClick={() => deleteExistingItem(item)} title="Удалить позицию">
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
          {!spec.items.length && <p className="muted">Позиции еще не добавлены.</p>}
        </div>
        <button className="primary" disabled={!spec.items.length} onClick={() => onPreview(spec)}>
          Предпросмотр
        </button>
      </div>
      <div className="main-panel">
        <PostscriptPanel spec={spec} templates={postscriptTemplates} onSave={savePostscriptSettings} />
        <h2>Добавить позицию</h2>
        <div className="form-grid">
          <label>
            Группа
            <select value={groupId} onChange={(event) => setGroupId(Number(event.target.value))}>
              {groups.map((group) => (
                <option value={group.id} key={group.id}>
                  {group.name.toUpperCase()}
                </option>
              ))}
            </select>
          </label>
          <label>
            {currentGroup?.refine_attribute_name || "Уточняющий признак"}
            <select value={refineValue} onChange={(event) => setRefineValue(event.target.value)}>
              {groupPositions.map((item) => (
                <option value={item.refine_value} key={item.id}>
                  {item.refine_value}
                </option>
              ))}
            </select>
          </label>
          <label>
            Количество
            <input value={quantity} onChange={(event) => setQuantity(event.target.value)} type="number" min="1" step="1" />
          </label>
            <button className="secondary icon-text" onClick={resolve}>
            <Search size={16} /> Определить
            </button>
        </div>
        {message && <div className="notice">{message}</div>}

        {ambiguousPositions.length > 0 && (
          <div className="match-list">
            {ambiguousPositions.map((match) => (
              <button className="match-card" key={match.id} onClick={() => preparePosition(match.id)}>
                <strong>{match.code}</strong>
                <span>{match.name}</span>
                <em>{currentGroup?.refine_attribute_name}: {match.refine_value}</em>
              </button>
            ))}
          </div>
        )}

        {position && (
          <>
            <div className="resolved">
              <Check size={18} />
              <div>
                <strong>{position.name}</strong>
                <span>
                  {position.code} · ОКПД-2 {position.okpd2_code || "не указан"}
                </span>
              </div>
            </div>
            <CharacteristicPicker characteristics={position.characteristics || []} selected={selected} onChange={setSelected} />
            <div className="form-actions">
              {editingItem && (
                <button className="ghost" onClick={resetEditorForm}>
                  Отменить
                </button>
              )}
              <button className="primary" disabled={!requiredDone} onClick={saveItem}>
                {editingItem ? "Сохранить" : "Добавить"}
              </button>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function Preview({ spec, onBack, onSaved }: { spec: TechnicalSpec; onBack: () => void; onSaved: (spec: TechnicalSpec) => void }) {
  const [message, setMessage] = useState("");
  const postscripts = postscriptLines(spec);

  async function save() {
    const updated = await api.updateSpec(spec.id, { status: "saved" });
    onSaved(updated);
    setMessage("ТЗ сохранено.");
  }

  async function download(format: "docx" | "xlsx" | "pdf") {
    setMessage("");
    try {
      const result = await api.exportSpec(spec.id, format);
      const link = document.createElement("a");
      link.href = result.url;
      link.download = "";
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Ошибка экспорта");
    }
  }

  return (
    <section className="workspace">
      <div className="toolbar">
        <button className="ghost" onClick={onBack}>
          Назад к редактированию
        </button>
        <div className="actions">
          <button className="secondary" onClick={save}>
            Готово
          </button>
          <button type="button" className="ghost icon-text" onClick={() => download("docx")}>
            <Download size={16} /> DOCX
          </button>
          <button type="button" className="ghost icon-text" onClick={() => download("xlsx")}>
            <Download size={16} /> XLSX
          </button>
          <button type="button" className="ghost icon-text" onClick={() => download("pdf")}>
            <Download size={16} /> PDF
          </button>
        </div>
      </div>
      {message && <div className="notice">{message}</div>}
      <div className="document-preview">
        <h2>{spec.title}</h2>
        {spec.items.map((item) => (
          <section className="doc-position" key={item.id}>
            <h3>Позиция {item.position_number}</h3>
            <table className="doc-meta">
              <tbody>
                <tr>
                  <th>N п/п</th>
                  <th>Наименование объекта закупки</th>
                  <th>Единица измерения</th>
                  <th>Кол-во</th>
                  <th>КТРУ</th>
                </tr>
                <tr>
                  <td>{item.position_number}</td>
                  <td>{item.object_name}</td>
                  <td>{item.unit_name}</td>
                  <td>{item.quantity}</td>
                  <td>{item.ktru_position_detail.code}</td>
                </tr>
              </tbody>
            </table>
            <div className="doc-requirements">
              Требования заказчика к объекту закупки по техническим, функциональным и качественным характеристикам, эксплуатационным характеристикам объекта закупки
            </div>
            <table className="doc-table">
              <tbody>
                <tr>
                  <th>Объект закупки</th>
                  <th>Наименование характеристики</th>
                  <th>Значение характеристики</th>
                  <th>Единица измерения</th>
                  <th>Инструкция по заполнению</th>
                </tr>
                {item.selected_characteristics.map((char, index) => (
                  <tr key={char.id}>
                    {index === 0 && <td rowSpan={item.selected_characteristics.length}>{item.object_name}</td>}
                    <td>{char.characteristic_name_snapshot}</td>
                    <td>{char.display_value}</td>
                    <td>{char.unit_name_snapshot}</td>
                    <td>{char.instruction_snapshot}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {postscripts.length > 0 && (
              <ol className="doc-postscripts">
                {postscripts.map((line, index) => (
                  <li key={`${line}-${index}`}>{line}</li>
                ))}
              </ol>
            )}
          </section>
        ))}
      </div>
    </section>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [screen, setScreen] = useState<Screen>("auth");
  const [specs, setSpecs] = useState<TechnicalSpec[]>([]);
  const [groups, setGroups] = useState<KtruGroup[]>([]);
  const [postscriptTemplates, setPostscriptTemplates] = useState<PostscriptTemplate[]>([]);
  const [search, setSearch] = useState("");
  const [currentSpec, setCurrentSpec] = useState<TechnicalSpec | null>(null);
  const [error, setError] = useState("");

  async function loadSpecs() {
    const list = await api.specs(search);
    setSpecs(list);
  }

  async function loadCurrentSpec(id: number) {
    const spec = await api.previewSpec(id);
    setCurrentSpec(spec);
    await loadSpecs();
    return spec;
  }

  async function bootstrap() {
    if (!api.token) return;
    try {
      const profile = await api.me();
      setUser(profile);
      setScreen(profile.is_approved || profile.is_staff ? "list" : "pending");
      const [specList, groupList, templateList] = await Promise.all([api.specs(), api.groups(), api.postscriptTemplates()]);
      setSpecs(specList);
      setGroups(groupList);
      setPostscriptTemplates(templateList);
    } catch {
      api.clearToken();
      setScreen("auth");
    }
  }

  useEffect(() => {
    bootstrap();
  }, []);

  useEffect(() => {
    if (screen === "list" && user) {
      loadSpecs().catch((err) => setError(err.message));
    }
  }, [search]);

  async function afterLogin(profile: User) {
    setUser(profile);
    if (!profile.is_approved && !profile.is_staff) {
      setScreen("pending");
      return;
    }
    setScreen("list");
    const [specList, groupList, templateList] = await Promise.all([api.specs(), api.groups(), api.postscriptTemplates()]);
    setSpecs(specList);
    setGroups(groupList);
    setPostscriptTemplates(templateList);
  }

  if (screen === "auth") return <AuthScreen onLogin={afterLogin} />;
  if (screen === "pending") {
    return (
      <main className="auth-shell">
        <div className="auth-panel">
          <h1>Аккаунт ожидает одобрения</h1>
          <p className="muted">Администратор должен одобрить заявку в Django Admin.</p>
          <button
            className="ghost"
            onClick={() => {
              api.clearToken();
              setScreen("auth");
            }}
          >
            Выйти
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="app-shell">
      {user && (
        <AppHeader
          user={user}
          onLogout={() => {
            api.clearToken();
            setUser(null);
            setScreen("auth");
          }}
        />
      )}
      {error && <div className="notice">{error}</div>}
      {screen === "list" && (
        <SpecList
          specs={specs}
          search={search}
          setSearch={setSearch}
          onCreate={async (title) => {
            const spec = await api.createSpec(title);
            setCurrentSpec(spec);
            if (!groups.length) setGroups(await api.groups());
            if (!postscriptTemplates.length) setPostscriptTemplates(await api.postscriptTemplates());
            setScreen("editor");
            await loadSpecs();
          }}
          onOpen={(spec) => {
            setCurrentSpec(spec);
            setScreen("editor");
          }}
          onCopy={async (id) => {
            await api.copySpec(id);
            await loadSpecs();
          }}
          onDelete={async (id) => {
            await api.deleteSpec(id);
            await loadSpecs();
          }}
          onRefresh={loadSpecs}
        />
      )}
      {screen === "editor" && currentSpec && (
        <Editor
          spec={currentSpec}
          groups={groups}
          postscriptTemplates={postscriptTemplates}
          onBack={() => setScreen("list")}
          onPreview={(spec) => {
            setCurrentSpec(spec);
            setScreen("preview");
          }}
          onReload={loadCurrentSpec}
        />
      )}
      {screen === "preview" && currentSpec && (
        <Preview
          spec={currentSpec}
          onBack={() => setScreen("editor")}
          onSaved={(spec) => {
            setCurrentSpec(spec);
            loadSpecs();
          }}
        />
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
