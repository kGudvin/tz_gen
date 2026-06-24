export type User = {
  id: number;
  email: string;
  role: "admin" | "user";
  is_approved: boolean;
  is_staff: boolean;
};

export type KtruGroup = {
  id: number;
  name: string;
  refine_attribute_name: string;
  positions_count: number;
};

export type KtruValue = {
  id: number;
  value: string;
  display_order: number;
};

export type KtruCharacteristic = {
  id: number;
  name: string;
  is_required: boolean;
  is_multiple_choice: boolean;
  unit_name: string;
  instruction: string;
  display_order: number;
  group_title: string;
  values: KtruValue[];
};

export type KtruPosition = {
  id: number;
  group: number;
  group_name: string;
  code: string;
  name: string;
  okpd2_code: string;
  okpd2_name: string;
  unit_name: string;
  is_enlarged: boolean;
  is_refined: boolean;
  refine_value: string;
  characteristics?: KtruCharacteristic[];
};

export type ResolveRefinedConflict = {
  detail: string;
  matches: number;
  positions: KtruPosition[];
};

export type SelectedCharacteristic = {
  characteristic_id: number;
  selected_values: string[];
  is_active: boolean;
};

export type SpecCharacteristic = {
  id: number;
  ktru_characteristic: number;
  selected_values: string[];
  display_value: string;
  is_active: boolean;
  is_required_snapshot: boolean;
  characteristic_name_snapshot: string;
  unit_name_snapshot: string;
  instruction_snapshot: string;
};

export type SpecItem = {
  id: number;
  position_number: number;
  ktru_position: number;
  ktru_position_detail: KtruPosition;
  object_name: string;
  quantity: string;
  unit_name: string;
  display_order: number;
  selected_characteristics: SpecCharacteristic[];
};

export type PostscriptTemplate = {
  id: number;
  name: string;
  text: string;
  is_active: boolean;
};

export type TechnicalSpec = {
  id: number;
  title: string;
  status: "draft" | "saved";
  custom_postscript: string;
  postscript_templates: number[];
  postscript_template_details: PostscriptTemplate[];
  created_at: string;
  updated_at: string;
  items: SpecItem[];
};
