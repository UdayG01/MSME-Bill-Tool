export const todayISO = () => new Date().toISOString().slice(0, 10);

export const formatMoney = (value) =>
  (Number(value) || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
