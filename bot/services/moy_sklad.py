import os
from datetime import datetime as dt
from typing import Optional

from moysklad import MoySklad
from moysklad.http import MoySkladHttpClient
from moysklad.http.utils import ApiResponse
from moysklad.queries import Query, Search
from moysklad.urls import ApiUrlRegistry
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from bot.scheme.parts import PartOrder


class SupplyPosition(BaseModel):
    quantity: int = Field(..., description="Количество")
    price: float = Field(..., description="Цена")
    vat: int = Field(..., description="НДС")
    discount: float = Field(0, description="Скидка")
    assortment: dict = Field(..., description="Метаданные товара")


class MoySkladSDK(BaseModel):
    login: str = Field(os.getenv("MOYSKLAD_LOGIN"), description="Логин пользователя")
    password: str = Field(
        os.getenv("MOYSKLAD_PASSWORD"), description="Пароль пользователя"
    )
    pos_token: str = Field(
        os.getenv("MOYSKLAD_POS_TOKEN"), description="Токен POS-приложения"
    )
    moy_sklad: MoySklad = None
    methods: ApiUrlRegistry = None
    client: MoySkladHttpClient = None
    org_name: str = None
    counterparty_name: str = None
    currency_name: str = None
    store_name: str = None
    meta: dict = {}

    class Config:
        arbitrary_types_allowed = True

    def init(self):
        self.moy_sklad = MoySklad.get_instance(
            login=self.login, password=self.password, pos_token=self.pos_token
        )
        self.methods = self.moy_sklad.get_methods()
        self.client = self.moy_sklad.get_client()

    def _get_meta(self, entity: str, name: Optional[str] = None) -> dict:
        if entity in self.meta:
            return self.meta[entity]

        entities = self._list_entities(entity)
        names = [one.get("name") for one in entities.rows]
        if name:
            org_meta = [
                org.get("meta") for org in entities.rows if org.get("name") == name
            ]
            if len(org_meta) != 1:
                raise ValueError(
                    f"Найдено {len(org_meta)} сущностей с именем {name!r}: {org_meta}"
                )
            else:
                org_meta = org_meta[0]
        else:
            # Запросить пользовательский ввод
            print_txt = "\n".join([f"{i + 1}. {name}" for i, name in enumerate(names)])
            selected_org = int(
                input(
                    f"Доступные сущности:\n{print_txt}\nВыберите сущность (введите порядковый номер): "
                )
            )
            if selected_org < 1 or selected_org > len(entities.rows):
                raise ValueError("Неверный порядковый номер")
            org_meta = entities.rows[selected_org - 1].get("meta")

        self.meta[entity] = org_meta
        return org_meta

    def _create_product(self, part: PartOrder) -> dict:
        """Создать или обновить сущность товара"""
        payload = dict(
            name=part.part_name,
            code=part.part_number,
            article=part.part_number,
            supplier=dict(meta=self.counterparty),
            buyPrice=dict(value=part.price * 100, currency=dict(meta=self.currency)),
        )
        existing = self._list_entities("product", search=part.part_number)

        if len(existing.rows) == 0:
            resp = self._create_entity("product", data=payload)
            print(f"Создана сущность {part.part_number!r}")
            meta = resp.meta
        elif len(existing.rows) == 1:
            meta = existing.rows[0]["meta"]
            # Обновить существующую сущность
            product_id = existing.rows[0].get("id")
            for k, v in payload.items():
                if v != existing.rows[0].get(k):
                    resp = self._update_entity(
                        "product", entity_id=product_id, data=payload
                    )
                    print(f"Обновлена сущность {part.part_number!r}")
                    meta = resp.meta
                    break
        else:
            raise ValueError(
                f"Найдено {len(existing.rows)} сущностей с артикулом {part.part_number!r}:\n{existing.rows}"
            )

        return meta

    @property
    def organization(self):
        return self._get_meta("organization", self.org_name)

    @property
    def counterparty(self):
        return self._get_meta("counterparty", self.counterparty_name)

    @property
    def currency(self):
        return self._get_meta("currency", self.currency_name)

    @property
    def store(self):
        return self._get_meta("store", self.store_name)

    def create_supply(
        self,
        products: list[PartOrder],
        vat_enabled: bool = False,
        vat_included: bool = False,
        invoice_date: str = None,
        vat_rate: float = 0.0,
    ) -> ApiResponse:
        items_meta = [self._create_product(p) for p in products]
        payload = dict(
            vatEnabled=vat_enabled,
            vatIncluded=vat_included,
            rate=dict(currency=dict(meta=self.currency)),
            organization=dict(meta=self.organization),
            agent=dict(meta=self.counterparty),
            store=dict(meta=self.store),
            moment=self._format_date(invoice_date),
            positions=[
                self._create_supply_position(p, m, vat_rate).dict()
                for p, m in zip(products, items_meta)
            ],
        )
        resp = self._create_entity("supply", data=payload)
        print(f"Создана приемка {resp.data['name']} от {resp.data['moment']}")
        return resp

    def _list_entities(
        self, entity: str, search: Optional[str] = None
    ) -> list[ApiResponse]:
        return self.client.get(
            self.methods.get_list_url(entity),
            query=Query(Search(search)) if search else None,
        )

    def _create_entity(self, entity: str, data: dict):
        return self.client.post(self.methods.get_list_url(entity), data=data)

    def _update_entity(self, entity: str, entity_id: str, data: dict):
        return self.client.put(self.methods.get_by_id_url(entity, entity_id), data=data)

    def _create_supply_position(
        self, part: PartOrder, meta: dict, vat: float = 0.0
    ) -> SupplyPosition:
        return SupplyPosition(
            quantity=part.quantity,
            price=part.price * 100,
            vat=int(vat * 100),
            assortment=dict(meta=meta),
        )

    def _format_date(self, invoice_date: str) -> str:
        if invoice_date:
            return f"{invoice_date} 00:00:00"
        else:
            return dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    from bot.workers import pdf

    order = pdf.PdfOrderEuropeanAutospares(
        "/Users/rustem.galiullin/Downloads/SOW.12436.pdf", checksum=1698.9
    )
    order_items = order.run()

    sklad = MoySkladSDK(
        org_name="Test-dexpress",
        counterparty_name=order.supplier_name,
        currency_name=order.currency,
        store_name="Al Fada Dubai",
    )
    sklad.init()
    parts = [PartOrder(**item) for item in order_items.to_dict(orient="records")]
    sklad.create_supply(
        parts,
        vat_rate=order.vat,
        invoice_date=order_items["invoice_date"].iloc[0],
        vat_included=False,
        vat_enabled=True,
    )
