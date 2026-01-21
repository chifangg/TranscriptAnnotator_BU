import { server_address, type Annotation, type Category } from "../constants";

let categories: Category[] = $state([]);
let categoriesMap: Record<string, string[]> = $derived.by(() => {
    const map: Record<string, string[]> = {};
    for (const category of categories) {
      for (const assignment of category.annotations) {
        const key = `${assignment.transcriptFile}-${assignment.annotationId}`;
        if (!map[key]) {
          map[key] = [];
        }
        map[key].push(category.label);
      }
    }
    return map;
})

export const categoriesState = {
    get categories() {
        return categories;
    },
    get categoriesMap() {
        return categoriesMap;
    },

  async fetchCategories() {
    try {
      const res = await fetch(`${server_address}/categories`);
      if (!res.ok) throw new Error(await res.text());
      categories = await res.json();

    } catch (err) {
        console.log("Error fetching categories:", err);
    } 
  },

  async addCategory(newLabel: string) {
    if (!newLabel.trim()) return;
    try {
      const res = await fetch(`${server_address}/categories`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ label: newLabel.trim(), annotations: [] }),
      });
      if (!res.ok) throw new Error(await res.text());
      const created = await res.json();
      categories = [...categories, created];
      newLabel = "";
    } catch (err) {
        console.log("Error adding category:", err);
    } 
  },

  async saveEdit(label: string, editDraft: string) {
    if (!editDraft.trim()) return;
    try {
      const category = categories.find((c) => c.label === label);
      if (!category) throw new Error("Category not found");

      const payload = {
        label: editDraft.trim(),
        annotations: category.annotations,
      };

      const res = await fetch(
        `${server_address}/categories/${encodeURIComponent(label)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      if (!res.ok) throw new Error(await res.text());

      const updated = await res.json();
      categories = categories.map((c) => (c.label === label ? updated : c));
      editDraft = "";
    } catch (err) {
        console.log("Error saving category edit:", err);
    }
  },

  async deleteCategory(label: string) {
    // if (!confirm(`Delete category "${label}"?`)) return;
    try {
      const res = await fetch(
        `${server_address}/categories/${encodeURIComponent(label)}`,
        {
          method: "DELETE",
        }
      );
      if (!res.ok) throw new Error(await res.text());
      categories = categories.filter((c) => c.label !== label);
    } catch (err) {
      console.log("Error deleting category:", err);
    }
  },

  async addAnnotationToCategory(categoryLabel: string, transcriptName: string, annotation: Annotation){
    try {
      const category = categories.find((c) => c.label === categoryLabel);
      if (!category) throw new Error("Category not found");

      // Check if already in category
      const alreadyInCategory = category.annotations.some(
        (a) =>
          a.transcriptFile === transcriptName &&
          a.annotationId === annotation.id
      );

      if (alreadyInCategory) {
        alert(`Annotation already in category "${categoryLabel}"`);
        return;
      }

      // Add this annotation to the category
      const updatedAnnotations = [
        ...category.annotations,
        { transcriptFile: transcriptName, annotationId: annotation.id },
      ];

      console.log("Updated Annotations:", updatedAnnotations);
      const response = await fetch(
        `${server_address}/categories`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            label: categoryLabel,
            category: {
                label: categoryLabel,
                annotations: updatedAnnotations,
            }
          }),
        }
      );
      categories = categories.map((c) =>
        c.label === categoryLabel
          ? { ...c, annotations: updatedAnnotations }
          : c
      );

      if (!response.ok) throw new Error("Failed to add to category");

    } catch (err) {
      console.error("Error adding to category:", err);
      alert("Failed to add to category");
    } 

  },
  async removeCategoryFromAnnotation(categoryLabel: string, transcriptName: string, annotationId: number) {
    try {
      const category = categories.find((c) => c.label === categoryLabel);
      if (!category) throw new Error("Category not found");

      // Remove this annotation from the category
      const updatedAnnotations = category.annotations.filter(
        (a) => !(a.transcriptFile === transcriptName && a.annotationId === annotationId)
      );

      const response = await fetch(
        `${server_address}/categories`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            label: categoryLabel,
            category: {
                label: categoryLabel,
                annotations: updatedAnnotations,
            }
          }),
        }
      );

      if (!response.ok) throw new Error("Failed to remove from category");

      // Update local state
      const updated = await response.json();
      categories = categories.map((c) => (c.label === categoryLabel ? updated : c));
    } catch (err) {
      console.error("Error removing from category:", err);
      alert("Failed to remove from category");
    }
  }
}